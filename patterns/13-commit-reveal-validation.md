---
Authors: Cüneyt Öztürk (falsify) and Ceri John (Topeuph AI, ValiChord)
License: CC0-1.0
---

# Pattern 13 — PRML + commit-reveal validation for independence attestation

> **When to use:** You've pre-registered the threshold with PRML and want structural
> proof that independent evaluators couldn't coordinate their verdicts — not just a
> signed record of who ran it.

## The gap Pattern 11 (Sigstore) alone leaves open

Pattern 11 closes the execution integrity gap: it proves who ran the eval, when,
and against which exact artefacts. That is what PRML §8.1 calls execution attestation.

It does not close the independence gap. A single actor who controls every "validator"
identity can still:

- Run the eval many times with different seeds or configurations.
- Sign only the result that meets the threshold.
- Publish a clean eval log alongside a PRML lock; Sigstore's transparency log
  will faithfully record it.

Sigstore proves *who* ran it and *when*. It does not prevent the same party — or a
coordinated group — from selectively publishing their best result after seeing each
other's outcomes.

PRML §8.1 explicitly defers this problem. Pattern 11 closes the first gap. This
pattern addresses the second.

## What commit-reveal validation adds

ValiChord is a commit-reveal protocol built on Holochain where independent validators
each seal a hashed verdict *before any reveals happen*. The reveal window opens only
once all validators have committed. Because each commitment hash is recorded on a
public DHT before any result is visible, post-hoc coordination is structurally
impossible rather than just contractually prohibited.

Three layers stack:

| Layer | Tool | What it commits |
|---|---|---|
| Pre-registration | PRML / falsify | metric, comparator, threshold, dataset hash, seed |
| Eval attestation | valichord_attestation | Merkle root over per-sample outputs; binds reported aggregate to the underlying run |
| Independence attestation | ValiChord | blind multi-party verdicts; immutable HarmonyRecord on public DHT |

**What a `valichord_attestation` bundle contains:**

- `model_id`, `task_id`, `generated_at`, optional `repo_commit`
- `metrics` — the aggregate scores PRML's threshold applies to
- `outputs_merkle_root` — SHA-256 binary tree over all per-sample outputs; enables
  selective disclosure without publishing the full log
- `bundle_hash` — SHA-256 of the RFC 8785 (JCS) canonical encoding of the entire
  bundle; this binds the reported aggregate to this specific run
- `content_hash` — same, with the provenance block (`meta`) excluded; two runs that
  produced identical results share a `content_hash` even if timestamps differ

The `outputs_merkle_root` is what makes the aggregate verifiable. A verifier who
suspects sample omission can issue a challenge-response: they choose a random nonce,
the holder provides Merkle proof paths for the challenged samples (without revealing
the full log), and the verifier confirms each path reconstructs to `outputs_merkle_root`.

**What ValiChord's HarmonyRecord contains:**

- `outcome` — plurality vote across validators (Reproduced / PartiallyReproduced /
  FailedToReproduce / UnableToAssess)
- `agreement_level` — ExactMatch (≥90% Reproduced) / WithinTolerance (≥70%) /
  DirectionalMatch (≥50%) / Divergent / UnableToAssess
- `participating_validators` — public keys of all validators who committed and revealed
- `discipline`, `validation_duration_secs`

The HarmonyRecord is content-addressed and immutable once written to the DHT.

## End-to-end flow

### 1. Pre-register the claim

```bash
falsify init my-eval --template accuracy
# edit .falsify/my-eval/spec.yaml: metric, comparator, threshold, dataset_hash, seed
falsify lock my-eval
```

The lock produces `.falsify/my-eval/spec.lock.json`, binding the claim before the eval runs.

### 2. Run the eval and build an attestation bundle

```python
from valichord_attestation import build_bundle
import json

# Collect per-sample outputs from your harness
samples = [{"id": i, "output": result} for i, result in enumerate(eval_results)]

bundle = build_bundle(
    model_id="anthropic/claude-sonnet-4-6",
    task_id="my-eval/harmbench-q3-2026",
    raw_metrics=[{"key": "accuracy", "value": 0.847}],
    samples=samples,
    samples_total=len(samples),
    repo_commit="<git rev-parse HEAD>",
)

with open(".falsify/my-eval/bundle.json", "w") as f:
    json.dump(bundle.__dict__, f, indent=2)

print("bundle_hash:  ", bundle.bundle_hash)   # 64-char SHA-256 hex
print("content_hash: ", bundle.content_hash)  # excludes provenance block
```

For inspect_ai and lm-evaluation-harness, adapters extract sample-level outputs
automatically. See `valichord_attestation` documentation for `InspectAILogAdapter`
and `InspectEvalsAdapter`.

**Publish `bundle.json` alongside the dataset** (Zenodo, Hugging Face, etc.) so
validators can independently verify `outputs_merkle_root` by building their own bundle.
This is a separate commitment from `data_hash` — the bundle attests to the specific
run's outputs; `data_hash` identifies the data and code validators will download.

### 3. Create a ValiChord validation round

Submit a `ValidationRequest` to ValiChord using the SHA-256 of your data deposit
(code + dataset archive) as `data_hash`, and `data_access_url` pointing to where
validators can fetch it.

```bash
# Via ValiChord's HTTP API (requires a running ValiChord node)
curl -X POST http://<valichord-node>/submit_validation_request \
  -H 'Content-Type: application/json' \
  -d '{
    "data_hash_hex": "<sha256 of your data deposit archive>",
    "data_access_url": "https://zenodo.org/record/<your-deposit>",
    "num_validators_required": 3,
    "validation_tier": "Basic",
    "discipline": {"type": "MachineLearning"},
    "researcher_institution": "Your Institution"
  }'
```

Include a pointer to `bundle.json` in your data deposit or README so validators
know where to find the run's attestation bundle.

### 4. Validators reproduce blind

Each independent validator:

1. Fetches the code and dataset from `data_access_url`, verifies the download matches
   `data_hash`.
2. Runs the eval with the same model and seed.
3. Optionally builds their own `valichord_attestation` bundle and compares
   `outputs_merkle_root` against the researcher's published `bundle.json`.
4. Seals a hashed verdict to the ValiChord DHT — **before any other validator's
   verdict is visible**.

The sealed commitment is `SHA-256(msgpack(attestation) || 32-byte nonce)`. It is
recorded on the public DHT before the reveal window opens; changing the verdict
afterwards would require changing a hash that is already public.

### 5. Reveal window and HarmonyRecord

Once all required commitments are on the DHT, the reveal window opens automatically.
Each validator publishes their nonce and full attestation. The protocol verifies
`SHA-256(msgpack(attestation) || nonce) == prior_commitment_hash` for every reveal.

The resulting HarmonyRecord is written to the governance DHT. Its hash is stable:
same set of validator verdicts → same record content → same content-addressed entry.

### 6. Add attestation_uri to the PRML manifest

```yaml
# .falsify/my-eval/spec.yaml — add after the round completes
attestation_uri: "http://<valichord-node>/record?hash=<harmony_record_hash>"
```

Re-lock to bind the HarmonyRecord reference into the PRML commitment:

```bash
falsify lock my-eval
```

## What this actually proves

A reader holding the PRML lock + bundle + HarmonyRecord can verify:

1. **The claim was pre-registered** — PRML lock existed before the eval ran.
2. **The aggregate is traceable to a specific run** — `bundle_hash` binds reported
   metrics to per-sample outputs via the Merkle root; changing any sample changes the root.
3. **Validators committed before seeing any results** — commitment hashes appear on the
   DHT before the reveal window; their timestamps are public.
4. **No validator changed their verdict after committing** — each reveal is verified
   against its prior commitment hash via `SHA-256(attestation || nonce)`.
5. **The HarmonyRecord is tamper-evident** — content-addressed, immutable once written.
6. **Selective disclosure is possible** — verifier-controlled challenge-response: verifier
   chooses a nonce, holder provides Merkle proofs for the challenged samples without
   revealing the full log; verifier confirms each proof reconstructs to `outputs_merkle_root`.

## What this still doesn't cover

- **A validator who goes silent.** The blind commit prevents coordination but not
  withdrawal. A validator who commits and then refuses to reveal strands a round. The
  DHT makes the absence visible — a commitment with no corresponding reveal is public —
  but does not compel publication. PRML §8.1's selective non-publication concern applies
  here too.

- **Validators are not currently bound to a verified reproduction bundle.** ValiChord
  validators commit to a verdict (Reproduced / PartiallyReproduced / etc.) hashed with
  a nonce. They do not currently commit to a hash of their own run's attestation bundle.
  A validator who claims "Reproduced" but produced different per-sample outputs than the
  researcher would not be caught by the protocol alone. Building validators' own bundles
  and committing to their `bundle_hash` as part of the sealed verdict is a planned
  extension; it is not yet implemented.

- **The integration is manual today.** `valichord_attestation` (the attestation library)
  and ValiChord (the Holochain protocol) are independent systems with no shared code.
  The workflow above — publishing `bundle.json` alongside the dataset, using the data
  deposit SHA-256 as `data_hash`, reading the HarmonyRecord URL for `attestation_uri`
  — requires manual coordination. A dedicated integration layer that automates the
  handoff is planned; it is not yet shipped.

- **Model substitution inside the run.** Neither PRML nor ValiChord verifies that the
  model loaded during the eval matches the model named in the manifest. Record the
  model's content-addressed checkpoint hash in `model_version` (PRML) and in `meta`
  (bundle); have validators verify it before running.

## Cross-references

- [Pattern 11 — PRML + Sigstore for execution integrity](11-sigstore-execution.md):
  use alongside this pattern. Sigstore proves who ran it; ValiChord proves validators
  couldn't coordinate. They address different parts of §8.1 and are complementary.
- [Pattern 10 — Federated multi-producer evaluation](10-federated-eval.md): Pattern
  10's auditor-layer gap (no out-of-the-box tool; v0.3 roadmap is a centralised
  registry) is what ValiChord's HarmonyRecord fills structurally via DHT.
- [Pattern 4 — Dataset version pinning](04-dataset-pinning.md): always pin and verify
  `dataset.hash` before submitting to ValiChord; validators must reproduce against the
  same dataset.
- [Pattern 2 — Multi-seed evaluation](02-multi-seed-eval.md): build a separate
  attestation bundle per seed; `samples_total` makes the seed count explicit in each
  bundle.

## Further reading

- [ValiChord repository](https://github.com/topeuph-ai/ValiChord) — Holochain
  commit-reveal protocol source; four-DNA architecture, HarmonyRecord specification
- [`valichord_attestation` library](https://github.com/topeuph-ai/ValiChord/tree/main/valichord_attestation) — Python attestation bundle library; format spec v1.2, adapters, challenge-response
- [Attestation format v1.2 spec](https://github.com/topeuph-ai/ValiChord/blob/main/valichord_attestation/spec/attestation_format_v1.md)
- [Holochain](https://www.holochain.org/) — agent-centric distributed computing: each node
  maintains their own cryptographically signed source chain; shared state lives in a DHT
- [PRML §8.1](https://spec.falsify.dev/v0.1#section-8.1) — the selective non-publication
  and execution integrity gap this pattern partially addresses
