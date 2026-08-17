#!/usr/bin/env python3
"""
Pattern 13 — PRML + commit-reveal validation, made runnable.

Co-authored pattern (Cuneyt Ozturk / falsify  &  Ceri John / Topeuph AI, ValiChord).
This script turns the cookbook doc into an executable end-to-end demo of the three
layers, so the composition is a worked example rather than prose.

WHAT IS REAL vs MODELLED (read this first):
  Layer 1  Pre-registration   PRML       REAL — uses the published `falsify_prml`
                                          reference (canonicalize + manifest_hash).
  Layer 2  Eval attestation   bundle     REAL crypto — Merkle root over per-sample
                                          outputs, plus bundle_hash/content_hash as the
                                          valichord_attestation v1.2 format describes.
                                          NOTE: the Merkle tree here uses RFC 6962-style
                                          leaf/node domain separation (0x00/0x01 tags);
                                          shipped v1.2 hashes pairs bare, so the same
                                          samples produce a different root in the library.
                                          Domain separation is on ValiChord's v2 list, so
                                          this demo anticipates v2 rather than mirroring
                                          v1.2 byte-for-byte (thanks to Ceri John for
                                          catching it — falsify-cookbook#4).
                                          (JSON canonicalisation here is sorted-key/compact,
                                          a faithful stand-in for the bundle's RFC 8785 JCS.)
  Layer 3  Independence       ValiChord  REAL commit-reveal crypto, but run LOCALLY in
                                          this process. The production protocol runs across
                                          isolated Holochain nodes on a public DHT; here we
                                          simulate N validators in memory to show the
                                          mechanism. No Holochain, no network.

It then stages three independent tamper attempts — one per layer — and shows each
layer catching the attack the layers below it cannot:
  A) move the threshold after the run        -> PRML says TAMPERED
  B) swap one per-sample output              -> Merkle root no longer matches
  C) a validator flips its verdict post-hoc  -> reveal != prior commitment

Run:  python3 pattern13_prml_commit_reveal.py
Requires only the Python stdlib + the falsify_prml reference sitting alongside it.
"""

import hashlib
import json
import os
import sys

try:
    import falsify_prml as prml  # the real PRML reference (pip install falsify)
except ImportError:
    # fall back to a checkout of the falsify repo sitting next to falsify-cookbook
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../falsify-hackathon"))
    sys.path.insert(0, _repo)
    try:
        import falsify_prml as prml
    except ImportError:
        sys.exit("This demo needs the PRML reference. Run: pip install falsify")


# ----------------------------------------------------------------------------- utils
def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def jcs(obj) -> bytes:
    """Sorted-key, compact JSON — a faithful stand-in for the bundle's RFC 8785 JCS."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def line(c="-"):
    print(c * 76)


# ------------------------------------------------------- Layer 2: attestation bundle
def merkle_root(leaves: list[bytes]) -> str:
    """SHA-256 binary tree over per-sample outputs.

    Uses RFC 6962-style domain separation (0x00 leaf tag, 0x01 node tag).
    Shipped valichord_attestation v1.2 hashes pairs bare, so roots differ;
    see falsify-cookbook#4. This matches ValiChord's v2 direction.
    """
    if not leaves:
        return sha256_hex(b"")
    level = [hashlib.sha256(b"\x00" + leaf).digest() for leaf in leaves]  # leaf-tag 0x00
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])  # duplicate last on odd count
        level = [
            hashlib.sha256(b"\x01" + level[i] + level[i + 1]).digest()  # node-tag 0x01
            for i in range(0, len(level), 2)
        ]
    return level[0].hex()


def build_bundle(model_id, task_id, metrics, samples, generated_at, repo_commit):
    """Mirror of valichord_attestation.build_bundle: returns the v1.2 bundle dict.

    bundle_hash  = sha256(jcs(whole bundle))      -> binds aggregate to this run
    content_hash = sha256(jcs(bundle minus meta)) -> equal across runs w/ same results
    """
    leaves = [jcs({"id": s["id"], "output": s["output"]}) for s in samples]
    core = {
        "model_id": model_id,
        "task_id": task_id,
        "metrics": metrics,
        "outputs_merkle_root": merkle_root(leaves),
        "samples_total": len(samples),
    }
    meta = {"generated_at": generated_at, "repo_commit": repo_commit}
    content_hash = sha256_hex(jcs(core))
    full = {**core, "meta": meta}
    bundle_hash = sha256_hex(jcs(full))
    return {**full, "content_hash": content_hash, "bundle_hash": bundle_hash}


# ----------------------------------------------- Layer 3: blind commit-reveal (local)
def commit(verdict: str, nonce: bytes) -> str:
    """ValiChord sealed commitment: sha256(serialize(verdict) || 32-byte nonce)."""
    return sha256_hex(jcs({"outcome": verdict}) + nonce)


def harmony_record(reveals: list[dict]) -> dict:
    """Plurality vote across validators -> immutable, content-addressed record."""
    tally: dict[str, int] = {}
    for r in reveals:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    outcome = max(tally, key=tally.get)
    repro = tally.get("Reproduced", 0) / len(reveals)
    level = (
        "ExactMatch" if repro >= 0.90 else
        "WithinTolerance" if repro >= 0.70 else
        "DirectionalMatch" if repro >= 0.50 else
        "Divergent"
    )
    rec = {
        "outcome": outcome,
        "agreement_level": level,
        "participating_validators": sorted(r["pubkey"] for r in reveals),
        "discipline": "MachineLearning",
    }
    rec["record_hash"] = sha256_hex(jcs(rec))  # content-addressed
    return rec


# =============================================================================== run
def main():
    print()
    line("=")
    print("  PATTERN 13 — PRML + commit-reveal validation (runnable composition)")
    print("  PRML: real reference | bundle: real crypto | commit-reveal: local sim")
    line("=")

    # ---- Layer 1: pre-register the claim (REAL PRML) ----
    print("\n[1] PRE-REGISTRATION  — lock the bar before the eval runs (PRML)")
    manifest = {
        "version": "prml/0.1",
        "claim_id": "01900000-0000-7000-8000-0000000013a7",  # UUIDv7 — required by the schema
        "created_at": "2026-06-15T00:00:00Z",
        "metric": "accuracy",
        "comparator": ">=",
        "threshold": 0.80,
        "dataset": {"id": "harmbench-v2", "hash": "a" * 64},
        "seed": 42,
        "producer": {"id": "your-lab.dev"},
    }
    errs = prml.validate_manifest(manifest)
    assert not errs, errs
    locked_hash = prml.manifest_hash(manifest)
    print(f"    metric/comparator/threshold : accuracy >= 0.80")
    print(f"    PRML manifest sha256        : {locked_hash}")
    print(f"    -> the bar is sealed. moving it later breaks this hash.")

    # ---- Layer 2: run the eval, build the attestation bundle (REAL crypto) ----
    print("\n[2] EVAL ATTESTATION  — bind the reported aggregate to the actual run")
    samples = [{"id": i, "output": f"resp-{i}-{(i * 7) % 5}"} for i in range(20)]
    observed = 0.85  # producer-asserted aggregate; PRML does NOT prove this number
    bundle = build_bundle(
        model_id="anthropic/claude-sonnet-4-6",
        task_id="harmbench-q3-2026",
        metrics=[{"key": "accuracy", "value": observed}],
        samples=samples,
        generated_at="2026-06-15T10:00:00Z",
        repo_commit="c0ffee1",
    )
    print(f"    observed accuracy (asserted): {observed}")
    print(f"    outputs_merkle_root         : {bundle['outputs_merkle_root'][:32]}...")
    print(f"    bundle_hash                 : {bundle['bundle_hash'][:32]}...")
    print(f"    content_hash                : {bundle['content_hash'][:32]}...")
    print(f"    -> the {len(samples)} per-sample outputs are now bound to the aggregate.")

    # ---- Layer 3: independent validators reproduce blind (LOCAL commit-reveal) ----
    print("\n[3] INDEPENDENCE ATTESTATION  — N validators commit blind, then reveal")
    verdicts = [("val-A", "Reproduced"), ("val-B", "Reproduced"), ("val-C", "Reproduced")]
    commits = {}
    for pk, v in verdicts:
        nonce = hashlib.sha256(f"{pk}-secret".encode()).digest()  # deterministic for demo
        commits[pk] = {"hash": commit(v, nonce), "nonce": nonce, "verdict": v}
        print(f"    {pk} COMMIT  {commits[pk]['hash'][:24]}...  (verdict sealed, hidden)")
    print("    -- all committed; reveal window opens --")
    reveals = []
    for pk, v in verdicts:
        c = commits[pk]
        ok = commit(c["verdict"], c["nonce"]) == c["hash"]  # protocol re-checks every reveal
        print(f"    {pk} REVEAL  {c['verdict']:14s} commitment-check={'OK' if ok else 'FAIL'}")
        reveals.append({"pubkey": pk, "verdict": c["verdict"]})
    rec = harmony_record(reveals)
    print(f"    -> HarmonyRecord: {rec['outcome']} / {rec['agreement_level']}  "
          f"({rec['record_hash'][:16]}...)")

    # ---- bind the HarmonyRecord back into PRML and re-lock ----
    print("\n[4] BIND BACK  — add attestation_uri to the manifest and re-lock (PRML)")
    bound = {**manifest, "attestation_uri": f"valichord://record/{rec['record_hash']}"}
    print(f"    new PRML manifest sha256    : {prml.manifest_hash(bound)}")
    print(f"    -> the independence record is now part of the pre-registered commitment.")

    # ============================ THREE TAMPERS, ONE PER LAYER ============================
    print()
    line("=")
    print("  ADVERSARIAL: each layer catches what the layers below it cannot")
    line("=")

    # A) move the bar after the result (Layer 1 catches it)
    print("\n A) Someone lowers the threshold 0.80 -> 0.84 after seeing observed=0.85")
    moved = {**manifest, "threshold": 0.84}
    naive = prml.evaluate_predicate(observed, ">=", 0.84)
    print(f"    naive check (0.85 >= 0.84)  : {'PASS' if naive else 'FAIL'}  <- looks fine")
    print(f"    PRML hash vs locked          : "
          f"{'MATCH' if prml.manifest_hash(moved) == locked_hash else 'TAMPERED'}  "
          f"<- the bar was moved")

    # B) swap one per-sample output (Layer 2 catches it)
    print("\n B) Producer swaps one weak sample for a strong one, keeps the same 0.85")
    tampered_samples = [dict(s) for s in samples]
    tampered_samples[7]["output"] = "resp-7-better"
    new_root = merkle_root([jcs({"id": s["id"], "output": s["output"]}) for s in tampered_samples])
    print(f"    aggregate still reads        : 0.85  <- unchanged")
    print(f"    outputs_merkle_root          : "
          f"{'MATCH' if new_root == bundle['outputs_merkle_root'] else 'MISMATCH'}  "
          f"<- the run's samples changed")

    # C) a validator flips its verdict after seeing the others (Layer 3 catches it)
    print("\n C) val-C tries to flip 'Reproduced' -> 'FailedToReproduce' AFTER revealing")
    c = commits["val-C"]
    flipped_ok = commit("FailedToReproduce", c["nonce"]) == c["hash"]
    print(f"    reveal-vs-commitment check   : "
          f"{'OK' if flipped_ok else 'FAIL'}  <- the sealed hash was committed on 'Reproduced'")
    print(f"    -> the flip is rejected; the public commitment can't be re-opened.")

    print()
    line("=")
    print("  THE COMPOSITION IN ONE LINE")
    print("  PRML proves the BAR was set first. The bundle binds the aggregate to the")
    print("  actual run. ValiChord proves independent validators couldn't coordinate.")
    print("  Three different attacks; three different layers; one stacked guarantee.")
    line("=")
    print()


if __name__ == "__main__":
    main()
