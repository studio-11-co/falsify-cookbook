# Pattern 4 — Dataset version pinning

> **When to use:** Your benchmark has versions (HumanEval got `v2`, MMLU got de-contaminated, GSM8K had a leak fixed). You want to pin which one you committed against.

## The problem in one sentence

Two papers can both report "62% on HumanEval" against two different dataset revisions and you cannot tell which is which.

## The fix in two fields

```yaml
dataset: "humaneval"
dataset_hash: "sha256:7c33e0a4b2..."  # SHA-256 of the canonical bytes
```

`dataset` is the *name* (human-readable); `dataset_hash` is the *content commitment* (machine-verifiable). Pre-compute the hash once and paste it.

## How to compute the hash

For a single file:

```bash
sha256sum humaneval.jsonl
# 7c33e0a4b2... humaneval.jsonl
```

For a directory or multi-file dataset, you need a **canonicalisation step** so anyone re-deriving gets the same hash:

```bash
# Sort filenames, concat, hash
( cd dataset_dir && find . -type f | sort | xargs cat ) | sha256sum
```

This is fragile. Better: tar the directory deterministically:

```bash
tar --sort=name \
    --owner=0 --group=0 --numeric-owner \
    -cf - dataset_dir/ | sha256sum
```

Better still: if your benchmark is published on HuggingFace Datasets, use the platform's content SHA:

```python
from datasets import load_dataset
ds = load_dataset("openai/human-eval", split="test")
print(ds.info.dataset_size, ds.info.download_size)
# the dataset card on HF includes a `sha` field that pins the revision
```

Your manifest's `dataset_hash` then references that platform SHA explicitly:

```yaml
dataset: "openai/human-eval"
dataset_hash: "huggingface:revision-d8f3e1a2..."
```

We use `huggingface:` instead of `sha256:` here because the underlying hash is the platform's, not yours. The point is: anyone who reads your manifest must be able to fetch *exactly* the dataset you committed against.

## What goes wrong

**1. The dataset gets updated and you don't notice.** HumanEval `v1` and `v2` differ in 12 problem statements. If you committed `dataset: "humaneval"` without a hash, no one knows which revision your "62%" refers to. Always commit a hash; never commit just a name.

**2. You hash the un-canonicalised version.** You compute the hash of `humaneval.jsonl` after your local pre-processing (lowercase, whitespace strip). Your colleague re-derives against the original file and gets a different hash. Pin: hash the *canonical published bytes*, never your local working copy.

**3. The dataset is private.** If `dataset_hash` is `sha256:abc...` of a private file, no one can verify. Either:

- Publish the file (and live with the consequences)
- Publish a cryptographic commitment to the file structure (Merkle root of N samples) and keep the file private
- Accept the claim is internally meaningful but externally unverifiable

The third is OK for internal audits; not OK for public claims.

**4. Multi-language tokenisation drift.** A benchmark file with Unicode strings can produce different bytes depending on normalisation form (NFC vs NFD). Force NFC before hashing:

```bash
iconv -f UTF-8 -t UTF-8 humaneval.jsonl | uconv -f UTF-8 -t UTF-8 -x "::NFC;" | sha256sum
```

## What doesn't work

- **Pinning by URL.** URLs are not content-stable. The maintainers can update the file without changing the URL.

- **Pinning by paper version.** Papers reference datasets but don't carry their bytes. You need the bytes.

- **Hashing the schema (column names) instead of the content.** Schema-only hashes don't catch row-level changes. Hash everything.

## A note on benchmark contamination

`dataset_hash` makes contamination *detectable*, not *prevented*. A determined publisher can hash a clean eval set, run on a contaminated one, and report the clean hash. PRML §8.1 names this. v0.2 P-02 (`runner_attestation`) addresses it; v0.1 does not.

What `dataset_hash` does prevent: a *publisher* claiming they used dataset A when they actually ran on a different file they call "A". The content hash makes that lie immediately falsifiable.

## Next pattern

For CI-level verification: see [Pattern 5 — CI gate](05-ci-gate.md).
