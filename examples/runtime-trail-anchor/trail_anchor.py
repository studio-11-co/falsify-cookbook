#!/usr/bin/env python3
"""A pre-committed eval claim as record zero of a runtime evidence trail.

A runtime trail records what an agent or pipeline did. It cannot show that the bar
a result was judged against is the bar that was agreed before the run: if the
threshold is edited after a weak result, a check that reads the current threshold
still says PASS. This example writes a PRML claim (metric, comparator, threshold,
dataset hash, seed) as record zero of a generic trail and checks every later
verdict against that record.

What the anchor shows: the claim bytes used at check time are the bytes hashed in
record zero, or they are not (TAMPERED). It does not show that the run happened
after the claim was written, or that the observed value is correct.

Run:  pip install falsify  &&  python3 trail_anchor.py
"""
from __future__ import annotations

import copy
import falsify_prml as prml  # PRML reference implementation, ships in `falsify`

CLAIM = {
    "version": "prml/0.1",
    "claim_id": "01900000-0000-7000-8000-00000000a001",  # UUIDv7 (fixed so the output is reproducible)
    "created_at": "2026-10-05T00:00:00Z",
    "metric": "task_success_rate",
    "comparator": ">=",
    "threshold": 0.95,
    "dataset": {"id": "agent-eval-suite@v3", "hash": "a" * 64},
    "seed": 7,
    "producer": {"id": "example.org/runtime-trail-demo"},
}


def new_trail(claim):
    """Record zero is the anchor: the claim and its manifest hash, written before any action."""
    errors = prml.validate_manifest(claim)
    assert not errors, errors
    return [{"seq": 0, "kind": "claim_anchor", "manifest_hash": prml.manifest_hash(claim), "claim": copy.deepcopy(claim)}]


def append(trail, kind, **fields):
    trail.append({"seq": len(trail), "kind": kind, **fields})


def naive_check(current_claim, observed):
    """What a trail-only check does: compare the result with whatever threshold is configured now."""
    ok = prml.evaluate_predicate(observed, current_claim["comparator"], current_claim["threshold"])
    return "PASS" if ok else "FAIL"


def anchored_check(trail, current_claim, observed):
    """Re-hash the claim in use and compare it with record zero before evaluating anything."""
    if prml.manifest_hash(current_claim) != trail[0]["manifest_hash"]:
        return "TAMPERED"
    return naive_check(current_claim, observed)


def run(title, observed, edit_threshold_to=None):
    trail = new_trail(CLAIM)
    append(trail, "action", detail="agent run started")
    append(trail, "action", detail="agent run finished")
    append(trail, "measurement", metric=CLAIM["metric"], value=observed)
    current = copy.deepcopy(CLAIM)
    if edit_threshold_to is not None:  # the goalpost move, made after seeing the result
        current["threshold"] = edit_threshold_to
    naive, anchored = naive_check(current, observed), anchored_check(trail, current, observed)
    append(trail, "verdict", naive=naive, anchored=anchored)
    moved = "" if edit_threshold_to is None else f"  (threshold edited {CLAIM['threshold']:.2f} -> {edit_threshold_to:.2f} after the result)"
    print(f"{title:<24} observed {observed:.2f}{moved}")
    print(f"{'':<24} trail-only check: {naive:<8} anchored check: {anchored}")
    return naive, anchored


def main():
    print(f"record zero: {CLAIM['metric']} {CLAIM['comparator']} {CLAIM['threshold']} "
          f"· manifest {prml.manifest_hash(CLAIM)[:16]}…\n")
    results = [
        run("1. honest pass", 0.97),
        run("2. honest fail", 0.93),
        run("3. goalpost moved", 0.93, edit_threshold_to=0.90),
    ]
    assert results == [("PASS", "PASS"), ("FAIL", "FAIL"), ("PASS", "TAMPERED")], results
    print("\nThe trail-only check passes case 3; the anchored check returns TAMPERED,")
    print("because the claim in use no longer hashes to record zero.")


if __name__ == "__main__":
    main()
