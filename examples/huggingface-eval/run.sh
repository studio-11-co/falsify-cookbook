#!/usr/bin/env bash
# Lock all manifests (before the run), run lm-eval, verify each (after).
# Uses the PRML reference CLI:  npm install -g falsify-js js-yaml

set -euo pipefail

cd "$(dirname "$0")"

TASKS=(humaneval mmlu gsm8k)
MODEL=${MODEL:-"hf"}
MODEL_ARGS=${MODEL_ARGS:-"pretrained=meta-llama/Llama-3.1-8B-Instruct"}

# 1. Lock — writes a <task>.manifest.prml.sha256 sidecar next to each manifest
echo "locking manifests…"
for t in "${TASKS[@]}"; do
  falsify-js lock "${t}.manifest.yaml"
done

# 2. Run lm-eval
echo "running lm-eval…"
lm_eval \
  --model "${MODEL}" \
  --model_args "${MODEL_ARGS}" \
  --tasks "$(IFS=,; echo "${TASKS[*]}")" \
  --output_path ./results

# 3. Verify each manifest is intact (hash unchanged since lock; exit 3 = tampered)
echo "verifying…"
for t in "${TASKS[@]}"; do
  falsify-js verify "${t}.manifest.yaml"
done

echo "all manifests intact."
