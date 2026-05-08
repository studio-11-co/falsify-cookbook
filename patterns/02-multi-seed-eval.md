# Pattern 2 — Multi-seed eval claim

> **When to use:** You report mean ± std across N seeds. Common in RL, language model evals with stochastic decoding, or any eval with intentional non-determinism.

## The shape of the claim

You're not claiming "the model scored 0.92." You're claiming "across 5 seeds, the model scored 0.92 ± 0.03 on average, and we commit to evaluating success at mean ≥ 0.90."

This needs two PRML decisions before the run:

1. **What is the metric?** The mean? The median? The min? Pick one and be explicit.
2. **What is the threshold against?** The mean? Each individual seed? The 5th percentile? Pick one.

## Manifest

```yaml
prml_version: "0.1"
metric: "mean_accuracy_over_seeds"
threshold: 0.90
threshold_direction: ">="
dataset: "humaneval"
dataset_hash: "sha256:..."
model_version: "claude-3.5-sonnet@2025-10-01"
sample_size: 5             # number of seeds, NOT number of dataset samples
seed: 42                   # the *seed seed* — base from which derived seeds are computed
pre_registered: "2026-05-08T20:00:00Z"
```

The crucial decisions are encoded in:

- `metric: "mean_accuracy_over_seeds"` — a label only you control. Pick a convention and document it.
- `sample_size: 5` — note this is the **number of seeds**, not the eval set size. PRML's `sample_size` is generic; you decide what counts.
- `seed: 42` — the *base* seed. Your eval code derives seeds 42, 43, 44, 45, 46 from it deterministically.

## Run

```python
import hashlib, random, statistics
from falsify import lock_manifest

# 1. lock before the run
hash_ = lock_manifest("manifest.yaml")
print(hash_)
# sha256:...

# 2. run
base_seed = 42
scores = []
for i in range(5):
    seed = base_seed + i
    score = run_eval(seed=seed)
    scores.append(score)

# 3. aggregate
mean = statistics.mean(scores)
std  = statistics.stdev(scores)
print(f"reported value = {mean:.4f} ± {std:.4f}")

# 4. compare to threshold
threshold_met = mean >= 0.90
```

## What goes wrong

**1. Reporting `value` as "0.92 ± 0.03" in the manifest.** PRML's `value` field is a scalar. Two options:

- **Option A (recommended):** the manifest commits the *threshold and aggregation rule*. After the run, you publish the scalar `mean` separately, with the std as supplementary context.
- **Option B:** emit two manifests — one for `mean_accuracy_over_seeds` and one for `std_accuracy_over_seeds`. Two hashes.

Don't try to encode "0.92 ± 0.03" in one field; you'll hit canonicalisation issues immediately.

**2. Inconsistent seed derivation.** If your code says `seed = 42 + i` but a colleague's code says `seed = hash(42, i)`, you'll get different scores from the same manifest. Pin the seed-derivation function in the metric name itself (e.g. `metric: "mean_accuracy_seeds_42_to_46"`) or document it in the model card the manifest links to.

**3. Mid-run seed change.** You're 3 seeds in, one of them OOMs, you restart with a different list. Now your manifest's `sample_size: 5` and `seed: 42` no longer match what was run. Re-issue the manifest with a fresh `pre_registered` timestamp.

## What doesn't work

- **Hashing each per-seed run separately and aggregating hashes.** That's a different (and more complicated) protocol. Stay with one manifest, one hash, one claim.

- **Reporting only the seed that gave the best score.** That's selective publication. PRML §8.1 names this. The whole point of multi-seed is to commit *before* you know which seed wins.

- **Treating `sample_size` as the eval set size when you also report aggregation across seeds.** Pick one meaning per project. If the eval set size matters, encode it in `dataset_hash` (which already commits to the exact set) and use `sample_size` for seed count.

## A leaner alternative

If you only need the mean and don't care about std, you can skip multi-seed: pick one seed, run once, claim the result. Multi-seed is for cases where the run-to-run variance is part of the claim.

## Next pattern

If your eval is live (Elo / arena-style) rather than batch: see [Pattern 3 — Streaming Elo eval](03-streaming-elo.md).
