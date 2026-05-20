---
Authors: Cüneyt Öztürk (Studio 11, falsify)
License: CC0-1.0
---

# Pattern 11 — PRML + Sigstore for execution integrity

> **When to use:** You've pre-registered the threshold with PRML, and now you also want a tamper-evident record of *who ran the eval, when, and against which exact artefacts*. PRML alone names this gap explicitly in §8.1; Sigstore closes most of it.

## The gap PRML alone leaves open

A locked PRML manifest binds the *claim* (metric, comparator, threshold, dataset hash, seed, producer identity) to a SHA-256 before the run. That makes the *commitment* tamper-evident. It does **not** prove:

- That the eval was actually executed (vs. fabricated post-hoc).
- Which model checkpoint or runtime image ran it.
- Who, identifiable to a trusted issuer, produced the eval log.
- That the eval log file you're holding right now wasn't substituted later.

PRML §8.1 names this as "selective non-publication / execution integrity" and explicitly defers the problem. A determined publisher can pre-register, run on a different model, fabricate an eval log, and there is no PRML-internal check that catches it.

This is what Sigstore is for.

## What Sigstore adds

[Sigstore](https://www.sigstore.dev/) is a free, open-source signing service hosted by the Linux Foundation. Three components matter here:

- **`cosign`** — the CLI that signs and verifies arbitrary files (`sign-blob`).
- **Fulcio** — a free certificate authority that issues short-lived signing certificates tied to an OIDC identity (GitHub Actions identity, Google account, Microsoft account, etc.).
- **Rekor** — an append-only transparency log that records every signature publicly. You don't need to trust the producer's claim of "I signed this on date X" — anyone can re-derive it from Rekor.

The keyless flow means there is no long-lived signing key sitting on a runner. The signature embeds the identity that produced it ("github.com/your-org/your-repo at commit abc123" or "alice@example.com via Google OIDC") and is logged publicly within seconds.

For PRML this gives you two signed artefacts per eval run:

1. The `.lock.json` (the locked PRML manifest), signed at lock-time.
2. The eval log JSON, signed immediately after the run completes.

Both signatures land in Rekor with timestamps that an auditor can re-verify offline.

## End-to-end flow

This is a runnable example assuming you have `falsify`, `cosign`, and either GitHub Actions OIDC or a local Sigstore identity available.

### 1. Pre-register and lock

```bash
# Create + edit the manifest
falsify init harmbench-q3-2026 --template accuracy
$EDITOR .falsify/harmbench-q3-2026/spec.yaml

# Lock — produces .falsify/harmbench-q3-2026/spec.lock.json
falsify lock harmbench-q3-2026
```

### 2. Sign the locked manifest

The lock step has already produced the canonical hash. Now bind it to a verifiable identity.

```bash
cosign sign-blob \
  --yes \
  --bundle .falsify/harmbench-q3-2026/spec.lock.cosign.bundle \
  .falsify/harmbench-q3-2026/spec.lock.json
```

The `--bundle` file contains the certificate, the signature, and the Rekor inclusion proof. Commit it alongside the lock.

In GitHub Actions the identity is automatic (workflow + repo + ref). Locally you'll be prompted to authenticate via OIDC; the resulting certificate names your account.

### 3. Run the eval

```bash
falsify run harmbench-q3-2026 > eval-log.json
```

`falsify run` records the experiment output to disk. The exact path is `.falsify/harmbench-q3-2026/runs/<timestamp>/eval-log.json` by default.

### 4. Sign the eval log

```bash
cosign sign-blob \
  --yes \
  --bundle .falsify/harmbench-q3-2026/runs/<timestamp>/eval-log.cosign.bundle \
  .falsify/harmbench-q3-2026/runs/<timestamp>/eval-log.json
```

Two signed bundles now exist: one for the pre-run commitment, one for the post-run result.

### 5. Verify (any reader, offline)

```bash
# 1. PRML hash check — does the lock still match the canonical bytes?
falsify verdict harmbench-q3-2026
# exit 0 PASS, 3 TAMPER, 10 FAIL

# 2. Lock signature — was this lock produced by the expected identity?
cosign verify-blob \
  --bundle .falsify/harmbench-q3-2026/spec.lock.cosign.bundle \
  --certificate-identity-regexp 'https://github\.com/your-org/your-repo/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  .falsify/harmbench-q3-2026/spec.lock.json

# 3. Eval-log signature — same expected identity?
cosign verify-blob \
  --bundle .falsify/harmbench-q3-2026/runs/<timestamp>/eval-log.cosign.bundle \
  --certificate-identity-regexp 'https://github\.com/your-org/your-repo/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  .falsify/harmbench-q3-2026/runs/<timestamp>/eval-log.json
```

All three must pass. Any one failing fails the audit chain.

## GitHub Actions reference workflow

```yaml
name: PRML + Sigstore eval
on: [pull_request, push]

permissions:
  contents: read
  id-token: write   # required for keyless Sigstore signing

jobs:
  eval:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: pip install falsify==0.1.4

      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      # Lock and sign the manifest (idempotent if already locked)
      - run: falsify lock harmbench-q3-2026
      - name: Sign locked manifest
        run: |
          cosign sign-blob --yes \
            --bundle .falsify/harmbench-q3-2026/spec.lock.cosign.bundle \
            .falsify/harmbench-q3-2026/spec.lock.json

      # Run the eval
      - run: falsify run harmbench-q3-2026
      - name: Sign eval log
        run: |
          LOG=$(ls .falsify/harmbench-q3-2026/runs/*/eval-log.json | tail -1)
          cosign sign-blob --yes \
            --bundle "${LOG%.json}.cosign.bundle" \
            "$LOG"

      # CI gate — verdict must pass and both signatures must verify
      - uses: studio-11-co/prml-verify-action@v1
        with:
          mode: verdict
          claim: harmbench-q3-2026
```

## What this actually proves

After running this pattern, an auditor in 2031 holds:

- `spec.yaml` (the PRML manifest text)
- `spec.lock.json` (the SHA-256 + canonical bytes proof)
- `spec.lock.cosign.bundle` (signature + Rekor proof of *who* locked it, and *when*)
- `eval-log.json` (the result)
- `eval-log.cosign.bundle` (signature + Rekor proof of *who* ran it, and *when*)

They can verify the PRML hash arithmetically with any of the four reference implementations. They can verify both Sigstore bundles by checking Rekor's public log — no producer trust required. The combination establishes:

1. The claim was committed before the run (PRML).
2. The commitment hasn't been edited since (PRML hash).
3. The lock was produced by a specific identity at a specific time (Sigstore).
4. The eval log was produced by the same identity shortly after (Sigstore).
5. Neither artefact has been substituted since (Sigstore + Rekor inclusion).

That's the closest thing to "this evaluation actually happened as described" you can get with free, open infrastructure.

## What this still doesn't cover

- **Model substitution inside the run.** If the runner loads model B when the manifest names model A, neither PRML nor Sigstore catches it. The mitigation is to record the model's content-addressed hash in the manifest's `model_version` field (or `model.hash` in v0.2) and have the runtime refuse to load anything else. That's a runtime concern, not a commitment concern.
- **Insider with workflow-write access.** Anyone who can modify the workflow can sign whatever they want with the org's identity. Branch protection on the workflow file + required reviewers reduces this; nothing eliminates it.
- **Time-of-check vs. time-of-use on the dataset.** The manifest pins `dataset.hash`; the runner has to actually verify that hash against the dataset it loads. `falsify` does this for built-in dataset references; for custom datasets you need the equivalent check in your code.

## Cross-references

- [Pattern 5 — CI gate via `prml-verify-action`](05-ci-gate.md): use the cosign verification steps above as additional CI steps inside that pattern's workflow.
- [Pattern 6 — Public registry anchoring](06-registry-anchor.md): registry anchoring + Sigstore are complementary, not redundant. The registry says "this hash existed publicly at time T"; Sigstore says "this hash was produced by identity I at time T."
- [Pattern 4 — Dataset version pinning](04-dataset-pinning.md): Sigstore-signing your dataset content hash file gives you the same identity binding for the dataset itself.

## Further reading

- [Sigstore documentation](https://docs.sigstore.dev/)
- [`cosign sign-blob` reference](https://docs.sigstore.dev/cosign/signing/signing_with_blobs/)
- [Rekor transparency log](https://docs.sigstore.dev/rekor/overview/)
- [SLSA framework](https://slsa.dev/) — the broader supply-chain framework Sigstore plugs into; PRML lives in SLSA's "provenance" slot, scoped to evaluation evidence rather than build artefacts.
