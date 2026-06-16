#!/usr/bin/env python3
"""
lm-evaluation-harness  <->  PRML bridge — runnable.

Backs the technical comment left on EleutherAI/lm-evaluation-harness PR #3752
(2026-06-11) with working code: turn an lm-eval run into a pre-registered PRML claim.

THE HONEST DESIGN (this matters):
  PRML *pre-registers the bar BEFORE the run*. A bridge that only reads a results
  JSON and then hashes it would be exactly the "compute the hash after the run"
  anti-pattern the cookbook warns against (anti/A1). So this bridge has two halves:

    lock   — BEFORE you run: build a PRML manifest from the lm-eval *task config*
             (metric, task identity, seed, n-shot) plus a threshold YOU choose, and
             lock it to a SHA-256. The bar is sealed before any result exists.
    verify — AFTER you run: read the lm-eval results JSON, pull the observed metric,
             and check it against the pre-locked manifest. Exit 0 PASS / 10 FAIL /
             3 TAMPERED (if the manifest was edited after locking).

What is real vs modelled:
  - PRML canonicalisation + hashing + verdicts: REAL `falsify_prml` reference.
  - The lm-eval results dict: a faithful in-file sample matching the real schema
    (results[task]["<metric>,<filter>"], config, versions, git_hash), so this runs
    with no lm-eval install. Point --results at a real results.json and it works the same.

Honest limit: lm-eval does not emit a content hash of the underlying dataset. For a
real pre-registration, pin the dataset archive's SHA-256 yourself (cookbook Pattern 4)
and pass it with --dataset-hash; here we derive a stable id from task+version+n-shot
and use a clearly-labelled placeholder hash so the demo is self-contained.

Run:  python3 lm_eval_to_prml.py          # runs lock -> (simulated run) -> verify
Requires only the stdlib + the falsify_prml reference (pip install falsify).
"""

import argparse
import json
import os
import sys

try:
    import falsify_prml as prml
except ImportError:
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../falsify-hackathon"))
    sys.path.insert(0, _repo)
    try:
        import falsify_prml as prml
    except ImportError:
        sys.exit("Needs the PRML reference. Run: pip install falsify")


# A faithful sample of an lm-eval results JSON (real schema, trimmed).
SAMPLE_RESULTS = {
    "results": {
        "hellaswag": {
            "alias": "hellaswag",
            "acc,none": 0.5712,
            "acc_stderr,none": 0.0049,
            "acc_norm,none": 0.7843,
            "acc_norm_stderr,none": 0.0041,
        }
    },
    "versions": {"hellaswag": 1.0},
    "n-shot": {"hellaswag": 10},
    "config": {
        "model": "hf",
        "model_args": "pretrained=gpt2",
        "batch_size": "8",
        "device": "cuda:0",
        "random_seed": 1234,
        "numpy_seed": 1234,
        "torch_seed": 1234,
    },
    "git_hash": "a1b2c3d",
}


def task_identity(results: dict, task: str) -> tuple[str, int, int]:
    """Stable dataset id from task + version + n-shot (not a content hash)."""
    ver = results.get("versions", {}).get(task, "?")
    nshot = results.get("n-shot", {}).get(task, 0)
    return f"lm-eval/{task}@v{ver}/{nshot}-shot", ver, nshot


def observed_metric(results: dict, task: str, metric: str) -> float:
    """Pull results[task]['<metric>,none'] — lm-eval keys metrics as 'metric,filter'."""
    row = results["results"][task]
    for key in (f"{metric},none", metric):
        if key in row:
            return float(row[key])
    have = [k for k in row if not k.endswith("_stderr,none") and k != "alias"]
    sys.exit(f"metric '{metric}' not in task '{task}'. available: {have}")


def build_manifest(results, task, metric, comparator, threshold, dataset_hash, seed):
    ds_id, _, _ = task_identity(results, task)
    return {
        "version": "prml/0.1",
        "claim_id": f"{task}-{metric}",
        "created_at": "2026-06-16T00:00:00Z",
        "metric": metric,
        "comparator": comparator,
        "threshold": float(threshold),
        "dataset": {"id": ds_id, "hash": dataset_hash},
        "seed": int(seed),
        "producer": {"id": "your-lab.dev"},
    }


def cmd_lock(args):
    results = load_results(args.results)
    # seed: prefer the lm-eval random_seed if present
    seed = args.seed if args.seed is not None else results.get("config", {}).get("random_seed", 0)
    m = build_manifest(results, args.task, args.metric, args.comparator,
                       args.threshold, args.dataset_hash, seed)
    errs = prml.validate_manifest(m)
    if errs:
        sys.exit("invalid manifest: " + "; ".join(errs))
    h = prml.manifest_hash(m)
    out = {"manifest": m, "locked_sha256": h}
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
    print(f"  task        : {m['dataset']['id']}")
    print(f"  bar locked  : {m['metric']} {m['comparator']} {m['threshold']}  seed={m['seed']}")
    print(f"  PRML sha256 : {h}")
    print(f"  -> bar sealed BEFORE the run. moving it later breaks this hash.")
    return out


def cmd_verify(lock, args):
    results = load_results(args.results)
    m = lock["manifest"]
    # 1) tamper check: re-hash the manifest; must equal what was locked
    if prml.manifest_hash(m) != lock["locked_sha256"]:
        print("  verdict     : TAMPERED (exit 3) — manifest changed after lock")
        return 3
    observed = observed_metric(results, m["claim_id"].rsplit("-", 1)[0], m["metric"])
    ok = prml.evaluate_predicate(observed, m["comparator"], m["threshold"])
    verdict = "PASS" if ok else "FAIL"
    code = 0 if ok else 10
    print(f"  observed    : {m['metric']} = {observed}")
    print(f"  bar         : {m['comparator']} {m['threshold']}")
    print(f"  verdict     : {verdict} (exit {code})")
    return code


def load_results(path):
    if not path:
        return SAMPLE_RESULTS
    with open(path) as f:
        return json.load(f)


def main():
    p = argparse.ArgumentParser(description="lm-eval <-> PRML bridge")
    p.add_argument("--results", help="lm-eval results.json (omit to use the built-in sample)")
    p.add_argument("--task", default="hellaswag")
    p.add_argument("--metric", default="acc_norm")
    p.add_argument("--comparator", default=">=")
    p.add_argument("--threshold", type=float, default=0.75)
    p.add_argument("--dataset-hash", default="b" * 64,
                   help="SHA-256 of the dataset archive (pin it yourself; see Pattern 4)")
    p.add_argument("--seed", type=int)
    p.add_argument("--out", help="write the lock file")
    p.add_argument("--mode", choices=["lock", "verify", "demo"], default="demo")
    args = p.parse_args()

    if args.mode == "lock":
        cmd_lock(args)
        return

    # demo: lock (before) -> run (already in SAMPLE_RESULTS) -> verify (after)
    print("\n" + "=" * 70)
    print("  lm-eval  ->  PRML  bridge   (lock before the run, verify after)")
    print("=" * 70)
    print("\n[LOCK] before the run — seal the bar from the task config")
    lock = cmd_lock(args)
    print("\n[RUN]  lm-eval produces results.json  (here: the built-in sample)")
    print(f"       observed acc_norm on hellaswag = "
          f"{observed_metric(SAMPLE_RESULTS, 'hellaswag', 'acc_norm')}")
    print("\n[VERIFY] after the run — check the result against the sealed bar")
    cmd_verify(lock, args)

    print("\n[ADVERSARIAL] someone lowers the threshold 0.75 -> 0.78 post-hoc")
    moved = json.loads(json.dumps(lock))
    moved["manifest"]["threshold"] = 0.78  # edit the manifest, keep the old locked hash
    rc = cmd_verify(moved, args)
    print(f"  -> naive check (0.7843 >= 0.78) would PASS, but the manifest hash no")
    print(f"     longer matches the lock, so the bridge returns TAMPERED (exit {rc}).")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
