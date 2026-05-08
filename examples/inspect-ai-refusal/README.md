# Example: Inspect AI refusal-rate eval, PRML pre-registered

> Uses the [`falsify-inspect`](https://github.com/studio-11-co/falsify-inspect) adapter. Pre-registers a refusal-rate threshold against HarmBench, then verifies the Inspect log post-run.

## What this shows

1. Use `falsify-inspect` to pre-register a refusal-rate claim before running an Inspect eval
2. Run the eval (produces an Inspect log JSON)
3. Re-derive the manifest hash from the log + caller-supplied threshold
4. CI gate that fails if the log is tampered (exit 3) or the threshold is missed (exit 10)

## Files

- [`run.py`](run.py) — Inspect eval driver wrapped with `falsify-inspect`
- [`manifest.yaml`](manifest.yaml) — readable PRML manifest (produced from the lock step)
- [`requirements.txt`](requirements.txt)

## Run it

```bash
pip install -r requirements.txt

python3 run.py
# 1. locks manifest, prints hash
# 2. runs inspect eval against HarmBench
# 3. extracts metadata from inspect log
# 4. re-derives hash; should match
# 5. exit 0 (pass) / 10 (fail) / 3 (tamper)
```

## Why this fits Inspect's data model cleanly

Inspect's `EvalSpec` already records `task`, `model`, `dataset.name`, `dataset.sha`, `config.epochs`, `config.seed`. The `falsify-inspect` adapter reads those fields out of the log JSON and matches them against your pre-registered manifest fields without modifying Inspect itself.

If the [upstream `PreRegistration` field RFC](../../../falsify-launch/outreach/INSPECT-AI-UPSTREAM-PR.md) is accepted, the adapter becomes redundant — the manifest hash will live inside `EvalSpec.pre_registration.manifest_hash` natively.

## See also

- [`falsify-inspect` repo](https://github.com/studio-11-co/falsify-inspect) (PyPI: `pip install falsify-inspect`)
- [Pattern 1 — Single-shot eval claim](../../patterns/01-single-shot-eval.md)
- [Pattern 5 — CI gate](../../patterns/05-ci-gate.md)
