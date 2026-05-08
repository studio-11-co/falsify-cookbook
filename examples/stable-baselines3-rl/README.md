# Example: Stable-Baselines3 + LunarLander-v2, multi-seed

> Pattern 2 — multi-seed eval claim. Mean episode reward across 5 seeds, threshold `>= 200`.

## What this shows

The HuggingFace Deep RL Course's Unit 1 ends with: "An episode is considered a solution if it scores at least 200 points." That's a textbook `threshold_direction: ">="` claim. Pre-register it.

This example:

1. Trains a PPO agent on LunarLander-v2 (≈1M steps)
2. Pre-registers `mean_episode_reward >= 200` over 5 seeds
3. Evaluates across `seeds = [42, 43, 44, 45, 46]`
4. Reports mean ± std + the locked hash

## Files

- [`train_and_eval.py`](train_and_eval.py) — PPO training + 5-seed eval
- [`manifest.yaml`](manifest.yaml) — multi-seed PRML manifest
- [`requirements.txt`](requirements.txt)

## Run it

```bash
pip install -r requirements.txt

# 1. Lock the manifest (before training!)
falsify lock manifest.yaml > manifest.hash

# 2. Train + eval
python3 train_and_eval.py
# trains for ~1M steps, then evaluates on seeds 42..46
# outputs: mean=205.3 ± 12.4, verdict=pass

# 3. Verify
falsify verify manifest.yaml --hash "$(cat manifest.hash)"
# OK
```

## Why pre-register *before* training

You could lock the manifest after training but before evaluation. The honest move is to lock *before training* — that way the `model_version` hash also commits to the architecture and hyperparams, not just the trained weights. If the run diverges (you tweak the LR mid-run), you re-issue with a fresh `pre_registered` timestamp.

## Anti-pattern: only publishing the best seed

The whole point of multi-seed is to commit *before* you know which seed wins. If you ran 20 seeds and report only the top 5, you've defeated the protocol. The manifest's `sample_size: 5` commits you to evaluating exactly 5 (and disclosing all 5).

## See also

- [Pattern 2 — Multi-seed eval claim](../../patterns/02-multi-seed-eval.md)
- [Anti-pattern A1 — Late hash](../../anti/A1-late-hash.md)
