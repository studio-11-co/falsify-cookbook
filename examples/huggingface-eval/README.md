# Example: HuggingFace `lm-eval-harness`, PRML pre-registered

> Pattern 1 + 4. Multi-task pre-registration: HumanEval + MMLU + GSM8K, three separate manifests, one CI workflow.

## What this shows

`lm-eval-harness` runs many evals. Each eval is a separate claim, so each gets its own PRML manifest. We show:

1. Three manifest files (one per benchmark)
2. A bash script that locks all three before invoking `lm_eval`
3. A post-run verification step that checks each `<task>.json` log against its manifest

## Files

- [`humaneval.manifest.yaml`](humaneval.manifest.yaml)
- [`mmlu.manifest.yaml`](mmlu.manifest.yaml)
- [`gsm8k.manifest.yaml`](gsm8k.manifest.yaml)
- [`run.sh`](run.sh) — lock-all → run lm-eval → verify-all
- [`requirements.txt`](requirements.txt)

## Run it

```bash
pip install -r requirements.txt

bash run.sh
# locks 3 manifests
# runs lm_eval --tasks humaneval,mmlu,gsm8k --model openai/gpt-4
# verifies each result against its manifest hash
```

## Why three manifests

Each manifest commits to one `(metric, threshold, dataset)` triple. PRML v0.1 is intentionally single-claim. Composing them into a "model card" of multiple PRML hashes is what model cards already do — model cards stay free-form prose; PRML hashes are the cryptographic anchors readers can re-derive.

## Dataset hash gotchas

`lm-eval-harness` pulls datasets from HuggingFace Datasets at run time. The dataset content can change without the URL changing. Pin the dataset SHA before running:

```bash
python3 -c "
from datasets import load_dataset
ds = load_dataset('openai/openai_humaneval', split='test')
print(ds.info.dataset_size, ds._info.dataset_name)
# include the HF revision SHA in your manifest's dataset_hash
"
```

## See also

- [Pattern 4 — Dataset version pinning](../../patterns/04-dataset-pinning.md)
- HF `lm-eval-harness`: https://github.com/EleutherAI/lm-evaluation-harness
