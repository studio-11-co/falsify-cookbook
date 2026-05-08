# Anti-pattern A3 — Storing private data in the manifest

> **The pattern:** You add internal customer IDs, internal threshold rationale, or trade-secret model details to the manifest "for completeness." Later you publish the hash. Whoever has the manifest now has your private data.

## Why it bites

The manifest is the *content*. The hash is the *commitment*. The hash alone tells the reader nothing about the manifest content; they must have the manifest itself to verify. **In practice, anyone using your hash as a citation will fetch the manifest.**

Two failure modes:

1. **You publish the manifest publicly** (e.g. in a model card). Anyone reading the model card sees the private data. This is just a confidentiality leak; PRML didn't cause it, but it didn't prevent it either.

2. **You don't publish the manifest, only the hash.** Now no one can verify your hash. The hash is meaningless without the manifest content, and you've defeated the entire purpose of pre-registration.

There is no third option where you "share the manifest privately with auditors only" and PRML's verifiability is preserved. Auditor-only access means non-auditors trust the auditor's word, not the math.

## How to spot it

Smell test: look at the manifest fields and ask of each one, "would I be comfortable if a journalist quoted this?" If the answer is no, the field shouldn't be in the manifest.

Common offenders:

- Customer IDs in `model_version` (`gpt-4-customer-acme-fine-tuned`)
- Internal team names in `dataset` (`teamX-private-eval-set`)
- Trade-secret thresholds (`threshold: 0.6_internal_only`)
- Free-form `note` fields with sensitive context

## How to fix

**Publish only what's structurally needed for verification.** PRML's eight fields are the minimum. They are:

- A metric name (public)
- A scalar value or null (public)
- A dataset name (public)
- A dataset hash (public; the hash, not the dataset)
- A model version label (public)
- A threshold + direction (public)
- A sample size (public)
- A seed (public)
- A pre-registration timestamp (public)

Anything beyond this list belongs in **separate documentation** that you control access to. Reference it from the manifest by URL or commit hash, but don't inline the content.

Example — instead of:

```yaml
metric: "accuracy"
threshold: 0.92
threshold_rationale: "We chose 0.92 because customer Acme requires 90%+ for procurement; we set 92% as our internal target to give a margin."
```

…use:

```yaml
metric: "accuracy"
threshold: 0.92
# (rationale documented in internal RFC https://internal.studio-11.co/rfc/12)
```

The internal RFC stays internal. The manifest stays publicly verifiable.

## A note on dataset names

Some publishers want to encode privacy in the dataset name itself: `dataset: "internal-eval-2026-Q2"`. This is fine *if* the corresponding `dataset_hash` matches a file you can publish later. If the file is permanently private:

- The hash is internally meaningful (you can re-derive it and check)
- The hash is externally meaningless (no one outside your org can verify)

That is a perfectly valid use of PRML for *internal audit*. It is not a valid use for public claims. Be honest about which you're doing.

## What about pseudonyms?

You can replace customer IDs with stable pseudonyms in the manifest:

```yaml
model_version: "claude-3.5-sonnet@2025-10-01"   # public — fine
model_version: "ftmodel-cust1234@v3"             # potentially private
model_version: "ftmodel-anon-9b2c@v3"            # pseudonymous — better, if anon mapping is internal
```

Pseudonymous IDs preserve the hash verifiability without leaking customer identity. The trade-off: anyone re-deriving from your manifest can verify *that* a model with this ID was committed; they cannot verify *which customer* it was. For most public claims, that's the right balance.

## See also

- [Pattern 6 — Public registry anchoring](../patterns/06-registry-anchor.md) for the "when to publish vs not" decision
- [Anti-pattern A4 — Hash as truth](A4-hash-as-truth.md) for related confusion about what the hash actually proves
