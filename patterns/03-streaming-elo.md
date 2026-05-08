# Pattern 3 — Streaming Elo / arena eval

> **When to use:** Your eval is *live* (Chatbot Arena, A/B-tested production, drift monitor). The "threshold" is a window-aggregated statistic, not a single number locked at one instant.

> **Spec status:** This pattern uses the **v0.2 streaming variant** (`prml_mode: streaming`). See [v0.2-rfc proposal P-01](https://spec.falsify.dev/v0.2-rfc#p-01-streaming-continuous-eval-variant). For v0.1-only deployments, fall back to Pattern 1 with a fixed window snapshot.

## The shape

You can't pre-register "Elo > 1300 in this exact run" because there is no run — there is a stream. You can pre-register:

- A **window** (`pre_registered_from` → `pre_registered_to`)
- A **value method** (how the live data gets aggregated into a number)
- A **minimum sample size** (below which the claim is undefined)
- A **threshold** that the windowed statistic must satisfy

## Manifest

```yaml
prml_version: "0.2"
prml_mode: "streaming"
metric: "elo_rating"
value_method: "lmsys_anonymous_chat_arena_v1"
threshold: 1300
threshold_direction: ">="
dataset: "lmsys-arena-live"
dataset_hash: "sha256:n/a-streaming"
model_version: "claude-3.5-sonnet@2025-10-01"
sample_size: 1000             # MINIMUM — claim undefined below this
seed: null                    # n/a for live streams
pre_registered_from: "2026-05-01T00:00:00Z"
pre_registered_to: "2026-06-01T00:00:00Z"
```

The hash commits to all of these together. The `value_method` field is a string identifier — point it at a documented aggregation method, not a vague label.

## Verification at the end of the window

When the window closes, anyone can:

1. Pull the public arena log from `pre_registered_from` to `pre_registered_to`
2. Apply the `value_method` aggregation rule
3. Compare to the `threshold`
4. Independently re-derive the manifest hash and confirm it matches the committed one

The freshness of the verification is bounded by how stale the public arena data is, not by any private state on your side.

## What goes wrong

**1. Picking a `value_method` that isn't documented.** "lmsys_anonymous_chat_arena_v1" is fine if there is a public document defining it. "our_internal_weighted_average_v3" is not — no one outside your org can re-derive. Either point at a public doc or use the v0.2 conformance vector format to publish your method alongside the manifest.

**2. Below the minimum sample size.** If `sample_size: 1000` and the window collected 700, the claim is undefined per spec. Many publishers want to "round up" — don't. Either re-issue the manifest with a smaller minimum, or accept the undefined verdict. Commitment integrity demands it.

**3. Window overlap.** You issue manifest A for May, manifest B for June, but your live system rolls out a model update on May 15. Now the May manifest's `model_version` no longer matches reality from May 15 onward. Either:

- Issue a new manifest at the rollout boundary (clean cut)
- Or commit to "claude-3.5-sonnet@*" with a wildcard convention you document elsewhere (less clean)

The wildcard form is not in spec. Use it cautiously.

**4. Treating the streaming hash as a single point-in-time commitment.** It isn't. It commits to *the rule by which the window will be evaluated* — you're committing to the protocol, not the answer.

## What doesn't work

- **Re-hashing partway through the window with updated stats.** That's not pre-registration. The hash is fixed at `pre_registered_from`; partial-window stats are observations, not claims.

- **Using streaming mode for batch evals.** If your eval has a defined start and end, use Pattern 1 or 2. Streaming mode adds complexity for cases where it's necessary, not for cases where it's flexible.

- **Streaming over an arbitrary aggregation method.** PRML can hash any method label; verifiability requires the method itself be reproducible. If your method depends on private data (production logs you don't share), the claim is internally meaningful but externally unverifiable.

## v0.1 fallback

If you must use v0.1 (e.g. JTC 21 input requires v0.1 stable spec), pick a representative window snapshot, treat it as a single-shot batch eval (Pattern 1), and re-issue at each new window. You lose continuous-eval semantics but gain v0.1 compatibility.

## Next pattern

If your dataset evolves (versioned benchmarks): see [Pattern 4 — Dataset version pinning](04-dataset-pinning.md).
