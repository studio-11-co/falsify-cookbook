# Pattern 9 — RLHF win-rate evaluations

> **When to use:** Reporting a win-rate from a judge-model comparison (AlpacaEval, MT-Bench, Arena-Hard) or a human-preference panel. The judge is usually GPT-4 or Claude; the panel is usually a Likert scale.

## The shape of the claim

You're claiming "model A wins ≥ 55% of the time against model B, judged by [X], over 805 prompts at temperature 0." Six commitments are in there:

1. Which two models (A vs B)
2. Which judge
3. Which prompt set
4. How many prompts
5. Decoding parameters
6. Threshold direction

If any of these is decided after seeing the result, the claim is post-hoc. PRML pins all six.

## Manifest

```yaml
version: prml/0.1
claim_id: 01900000-0000-7000-8000-000000000020
created_at: "2026-05-09T20:00:00Z"
metric: win_rate_against_baseline
comparator: ">="
threshold: 0.55
dataset:
  id: alpaca-eval-2-2024-08
  hash: huggingface:revision-d8f3e1a2
  uri: https://huggingface.co/datasets/tatsu-lab/alpaca_eval
seed: 42
producer:
  id: studio-11.co
model:
  id: experimental-rlhf-2026-05-09
notes: |
  AlpacaEval 2.0, judge: gpt-4-1106-preview, baseline: gpt-4-0613.
  805 prompts, temperature 0.0, single completion per prompt.
  Win-rate aggregated by length-controlled scoring (LC win-rate).
```

The judge identity, the baseline identity, and the aggregation method (length-controlled vs raw) all live in `notes`. They are part of the canonical bytes — tampering with them later breaks the hash.

## What goes wrong

**1. Judge model drift.** OpenAI silently retires `gpt-4-1106-preview`. You re-run, judge gives different scores, your old hash no longer corresponds to a runnable eval. The hash is still valid as a *commitment record*, but the eval is no longer reproducible. Mitigation: pick judges with stable identity (Claude `@2025-10-01`-style versioning) or judges that have an open-weight equivalent (Llama-Judge).

**2. Length-controlled vs raw confusion.** AlpacaEval 2.0 publishes both LC win-rate and raw win-rate. A claim of "55% win-rate" that doesn't specify which one is ambiguous. Always commit to one in `notes`. Better: encode it in the metric name itself (`length_controlled_win_rate`).

**3. Prompt set version drift.** AlpacaEval has had three versions. Pin the dataset hash; not just the name.

**4. Baseline identity matters more than the model.** The number is meaningless without knowing what you beat. `notes` must name the baseline build, not just "GPT-4".

**5. Tied judgements counted as wins.** Some scoring methods give ties to the model under test; some split them. Document the rule.

## What doesn't work

- **Reporting a single number without the comparison context.** "Our model achieves 67% win-rate" is meaningless. 67% against what, judged by whom?

- **Pre-registering the judge but not the baseline.** Both are in scope. The judge introduces one bias; the baseline introduces another.

- **Retrying with a different judge if the first one disagrees.** Pre-register one judge. Run once. If you genuinely want to check robustness across judges, pre-register a *list* of judges and report all results — not the favourable subset.

## Specific to RLHF win-rate

**Self-comparison is rarely useful.** "Our v3 wins 72% against our v2" is a shipping metric, not a research result. PRML records it the same as any other claim, but the audit value is limited because the publisher controls both sides of the comparison.

**Cross-publisher comparison requires coordination.** "Our model beats their model" implies running their model. Did the publisher have access to it at the same checkpoint the other publisher reports? The model SHA in the manifest's `model` field — for both models — is what closes that question. If you can't get the other publisher's exact SHA, your claim is bounded by the version drift you can't control.

**Judge-as-a-service evals (Chatbot Arena) need streaming mode.** v0.2 Pattern 3 covers this. Win-rate over a live stream is a window, not a batch.

## A worked failure mode (educational)

In 2024, several published RLHF papers reported win-rates against GPT-4 baselines without specifying which GPT-4 build. Independent re-runs against `gpt-4-0613` and `gpt-4-1106-preview` produced different numbers — sometimes by 8–10 percentage points. This wasn't dishonesty; it was an absence of pinning. PRML wouldn't have prevented the drift, but the manifests would have surfaced *which* GPT-4 was used in each run, making the ambiguity mechanically visible to readers.

## What this pattern doesn't fix

Selective publication still applies (PRML §8.1). A publisher running 50 RLHF variants and publishing only the top three is operating below the line of public accountability. PRML pins each variant's claim; it cannot compel publication of all of them.

## Tooling

```bash
falsify lock manifest.yaml
# run eval
falsify verify manifest.yaml --hash <hash>
```

For multi-judge robustness (more than one judge specified):

```yaml
metric: median_win_rate_across_judges
notes: |
  Judges: [gpt-4-1106-preview, claude-3.5-sonnet@2025-10-01, llama-3.1-70b-judge]
  Aggregation: median win-rate across the three judges per prompt.
```

The aggregation rule is part of `notes` and therefore part of the hash. Tampering with which judges to count breaks the hash.

## See also

- [Pattern 2 — Multi-seed eval claim](02-multi-seed-eval.md)
- [Pattern 3 — Streaming Elo eval](03-streaming-elo.md) (for live arena settings)
- [Pattern 4 — Dataset version pinning](04-dataset-pinning.md)
- [Anti-pattern A1 — Late hash](../anti/A1-late-hash.md)
