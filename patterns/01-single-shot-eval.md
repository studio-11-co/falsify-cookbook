# Pattern 1 — Single-shot eval claim

> **When to use:** One model. One benchmark. One number reported. The 90% case.

## What you're committing to

Before you run the eval, you commit nine things:

```yaml
prml_version: "0.1"
metric: "accuracy"
threshold: 0.92
threshold_direction: ">="
dataset: "imagenet-1k-val"
dataset_hash: "sha256:9e2c8d1a..."   # SHA-256 of the resized 50,000-image tarball
model_version: "resnet50-2026-05-08-fp16"
sample_size: 50000
seed: 42
pre_registered: "2026-05-08T20:00:00Z"
```

The hash of these fields is your receipt that the threshold (`>= 0.92`) was set before the run.

## Run it

```bash
pip install falsify
falsify lock manifest.yaml
# sha256:e3b0c44298fc1c14a...

# ...run your eval...

falsify verify manifest.yaml --hash sha256:e3b0c44298fc1c14a...
# OK
```

## What goes wrong

**1. The dataset hash drifts.** The most common screw-up. You compute `dataset_hash` against `imagenet-1k-val.tar`, the next day someone re-downloads the file and unpacks it in a different order, and `sha256sum` produces a different hash. Pin the *content*, not the path. Pre-compute once, paste into the manifest.

**2. Float precision.** `threshold: 0.92` and `threshold: 0.920` are different bytes. Pick one form for your project and stick with it. The reference impls handle this consistently — but your YAML editor may not.

**3. Pre-registration drift.** You commit at T=0, you start the run at T=2h. If something forces you to re-launch the eval at T=4h, the manifest still says T=0. That's correct: the *commitment* didn't change; only the run did. If you want to mark a re-run, emit a *new* manifest with a fresh `pre_registered` timestamp; don't edit the old one.

## What doesn't work

- **Hashing the model.** PRML does not (and shouldn't) commit to the model weights. `model_version` is a *label* — a stable identifier you control. Wrap PRML inside a Sigstore signature if you want artifact-level integrity.

- **Multiple thresholds in one manifest.** Pick one. If you have two metrics, emit two manifests with two hashes. This is by design — composite thresholds make pre-registration ambiguous.

- **Threshold direction left implicit.** "We hit ~92% accuracy" is not a PRML claim. PRML requires you to commit to `>= 0.92` or `<= 0.05` or whatever shape your direction takes.

## Minimal manifest skeleton (copy/paste)

```yaml
prml_version: "0.1"
metric: ""                 # e.g. "accuracy", "f1", "refusal_rate"
threshold: 0.0
threshold_direction: ">="  # >= | <= | > | < | ==
dataset: ""
dataset_hash: "sha256:"
model_version: ""
sample_size: 0
seed: 0
pre_registered: ""         # RFC 3339 UTC, e.g. "2026-05-08T20:00:00Z"
```

## Next pattern

If you report mean ± std across multiple seeds: see [Pattern 2 — Multi-seed eval claim](02-multi-seed-eval.md).
