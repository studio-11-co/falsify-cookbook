#!/usr/bin/env bash
# Lock all manifests, run lm-eval, verify each.

set -euo pipefail

cd "$(dirname "$0")"

TASKS=(humaneval mmlu gsm8k)
MODEL=${MODEL:-"hf"}
MODEL_ARGS=${MODEL_ARGS:-"pretrained=meta-llama/Llama-3.1-8B-Instruct"}

# 1. Lock
echo "locking manifests…"
for t in "${TASKS[@]}"; do
  falsify lock "${t}.manifest.yaml" > "${t}.manifest.hash"
  echo "  ${t}: $(cat "${t}.manifest.hash")"
done

# 2. Run lm-eval
echo "running lm-eval…"
lm_eval \
  --model "${MODEL}" \
  --model_args "${MODEL_ARGS}" \
  --tasks "$(IFS=,; echo "${TASKS[*]}")" \
  --output_path ./results

# 3. Verify each
echo "verifying…"
for t in "${TASKS[@]}"; do
  falsify verify "${t}.manifest.yaml" --hash "$(cat "${t}.manifest.hash")"
done

echo "all manifests intact."
