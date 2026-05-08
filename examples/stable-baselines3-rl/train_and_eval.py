#!/usr/bin/env python3
"""Train PPO on LunarLander-v2 and evaluate across 5 seeds with PRML pre-registration."""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
from pathlib import Path

# Production deps (uncomment when running):
#   import gymnasium as gym
#   from stable_baselines3 import PPO
#   from stable_baselines3.common.evaluation import evaluate_policy
#   from stable_baselines3.common.monitor import Monitor


HERE = Path(__file__).parent
MANIFEST = HERE / "manifest.yaml"
HASH_FILE = HERE / "manifest.hash"
RESULT_FILE = HERE / "eval-result.json"

SEEDS = [42, 43, 44, 45, 46]
N_EVAL_EPISODES = 100
TOTAL_TRAIN_STEPS = 1_000_000


def lock_manifest() -> str:
    r = subprocess.run(["falsify", "lock", str(MANIFEST)], capture_output=True, text=True, check=True)
    h = r.stdout.strip()
    HASH_FILE.write_text(h + "\n")
    return h


def train(seed: int = 42) -> "PPO":  # noqa: F821
    """Train a PPO policy on LunarLander-v2.

    Replace the body with real training:

        env = Monitor(gym.make("LunarLander-v2"))
        model = PPO("MlpPolicy", env, verbose=0, seed=seed)
        model.learn(total_timesteps=TOTAL_TRAIN_STEPS)
        return model
    """
    raise NotImplementedError("install stable-baselines3 and uncomment imports")


def eval_seed(model: "PPO", seed: int) -> float:  # noqa: F821
    """Return mean episode reward for one seed."""
    # eval_env = Monitor(gym.make("LunarLander-v2"))
    # eval_env.reset(seed=seed)
    # mean_reward, _ = evaluate_policy(model, eval_env, n_eval_episodes=N_EVAL_EPISODES, deterministic=True)
    # return float(mean_reward)
    raise NotImplementedError


def main() -> int:
    print("locking manifest…", file=sys.stderr)
    manifest_hash = lock_manifest()

    print("training…", file=sys.stderr)
    model = train(seed=SEEDS[0])

    print("evaluating across seeds…", file=sys.stderr)
    rewards = [eval_seed(model, s) for s in SEEDS]
    mean = statistics.mean(rewards)
    std = statistics.stdev(rewards) if len(rewards) > 1 else 0.0

    result = {
        "manifest_hash": manifest_hash,
        "metric": "mean_episode_reward_over_seeds",
        "seeds": SEEDS,
        "per_seed_rewards": rewards,
        "observed_value": mean,
        "observed_std": std,
        "threshold": 200.0,
        "threshold_direction": ">=",
        "verdict": "pass" if mean >= 200.0 else "fail",
    }
    RESULT_FILE.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

    subprocess.run(["falsify", "verify", str(MANIFEST), "--hash", manifest_hash], check=True)
    return 0 if result["verdict"] == "pass" else 10


if __name__ == "__main__":
    raise SystemExit(main())
