# PRML Cookbook

> Short, opinionated patterns for using PRML in real ML evaluation pipelines.

[![Spec](https://img.shields.io/badge/PRML-v0.1-39D98A.svg)](https://spec.falsify.dev/v0.1)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20177839-blue.svg)](https://doi.org/10.5281/zenodo.20177839)
[![License](https://img.shields.io/badge/license-CC0-blue.svg)](LICENSE)

This is the field-manual for the [PRML specification](https://spec.falsify.dev/v0.1). The spec tells you *what* a manifest is. The cookbook tells you *how* to use it without shooting yourself in the foot.

Every pattern is:

- **One page** — read in under three minutes
- **Self-contained** — the example runs end-to-end with the snippets shown
- **Failure-mode-first** — what goes wrong is named before what goes right

## Patterns

| # | Pattern | When to use |
|---|---|---|
| 1 | [Single-shot eval claim](patterns/01-single-shot-eval.md) | One model, one benchmark, one number — the 90% case. |
| 2 | [Multi-seed eval claim](patterns/02-multi-seed-eval.md) | When you report mean ± std over N seeds. |
| 3 | [Streaming Elo / arena eval](patterns/03-streaming-elo.md) | Live leaderboards. (Uses v0.2 streaming variant.) |
| 4 | [Dataset version pinning](patterns/04-dataset-pinning.md) | Benchmarks evolve; how to commit to a specific revision. |
| 5 | [CI gate via prml-verify-action](patterns/05-ci-gate.md) | Block PRs that ship a model with a tampered eval claim. |
| 6 | [Public registry anchoring](patterns/06-registry-anchor.md) | When and when not to publish your hash publicly. |
| 7 | [Revocation](patterns/07-revocation.md) | Withdrawing a manifest after publication. (v0.2 feature.) |
| 8 | [Pre-registration without infrastructure](patterns/08-no-infra.md) | The minimum-viable workflow: a YAML file and `sha256sum`. |
| 9 | [RLHF win-rate evaluations](patterns/09-rlhf-winrate.md) | Judge-model comparisons (AlpacaEval, MT-Bench, Arena-Hard). |
| 10 | [Federated evaluation](patterns/10-federated-eval.md) | Multi-org replication: shared hash, distinct producers, regulator-grade audit trail. |
| 11 | [PRML + Sigstore for execution integrity](patterns/11-sigstore-execution.md) | Closes the §8.1 gap: who ran the eval, when, against which exact artefacts. |
| 12 | [PRML in Hugging Face model cards](patterns/12-huggingface-model-card.md) | Make the accuracy number on a published HF model card verifiable, not trust-me prose. |
| 13 | [PRML + commit-reveal validation for independence attestation](patterns/13-commit-reveal-validation.md) ▶ [runnable](patterns/examples/) | Closes the other §8.1 gap: structural proof that independent evaluators couldn't coordinate verdicts. Co-authored with [ValiChord](https://github.com/topeuph-ai/ValiChord). |

## Anti-patterns

| # | Anti-pattern | Why it bites |
|---|---|---|
| A1 | [Computing the hash *after* the run](anti/A1-late-hash.md) | The whole point is committing before. |
| A2 | [Editing the manifest "to fix a typo"](anti/A2-typo-edit.md) | Any edit breaks the hash. Use revocation. |
| A3 | [Storing private data in the manifest](anti/A3-private-data.md) | The hash is published; the manifest content might be too. |
| A4 | [Treating the hash as proof of *truth*](anti/A4-hash-as-truth.md) | The hash proves *commitment*, not *correctness*. |

## Reference

- [Identity levels (0–4)](IDENTITY-LEVELS.md) — a non-normative ladder for the binding strength between `producer` and the real-world authoring entity. Used by Pattern 11 and the v0.3 RFC.


## Audit & compliance crosswalks

Subcategory-by-subcategory maps from major AI governance frameworks to PRML fields (FULL / PARTIAL / NONE tagged):

- [EU AI Act Article 12](https://spec.falsify.dev/eu-ai-act/article-12/) — code-level pattern for the 2 December 2027 high-risk deadline
- [NIST AI RMF 1.0](https://spec.falsify.dev/nist-ai-rmf/) — GOVERN / MAP / MEASURE / MANAGE subcategory map
- [ISO/IEC 42001:2023](https://spec.falsify.dev/iso-42001/) — AI Management System clause-by-clause evidence map

## Examples

Working code in [`examples/`](examples/):

- [`pytorch-imagenet/`](examples/pytorch-imagenet/) — Full example: PRML manifest before a PyTorch ImageNet eval, hash committed, post-run verification
- [`stable-baselines3-rl/`](examples/stable-baselines3-rl/) — RL agent on LunarLander-v2, mean episode reward claim, threshold direction `>=`
- [`inspect-ai-refusal/`](examples/inspect-ai-refusal/) — Refusal-rate eval via Inspect AI, PRML pre-registration via `falsify-inspect`
- [`huggingface-eval/`](examples/huggingface-eval/) — `lm-eval-harness` integration, multi-task pre-registration

## License

- Documentation, patterns, examples: **CC0 1.0** — public domain dedication. Mirror, fork, modify without attribution.
- Any tooling: **MIT**.

## Contributing

Pattern proposals welcome via PR. Each new pattern must:

1. Solve a real problem someone hit while implementing PRML
2. Be reproducible — name the tools and their versions
3. Include a "what doesn't work" section (we are not selling)
4. Be under 800 words

Open an issue first if you're unsure whether your pattern fits.

## Authors

Cüneyt Öztürk
Contact: hello@falsify.dev · [falsify.dev](https://falsify.dev)


---

## Status

- v0.1 stable. v0.2 RFC open through 2026-05-22 — [spec.falsify.dev/v0.2-rfc](https://spec.falsify.dev/v0.2-rfc).
- The PRML JSON Schema is in the [SchemaStore catalog](https://www.schemastore.org/json/) (merged 2026-05-11), so `*.prml.yaml` files autocomplete in VS Code, JetBrains, Helix, Zed, and Cursor out of the box.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) and the [`good first issue`](https://github.com/studio-11-co/falsify-cookbook/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22) label for scoped work.

**Cite the spec:** Öztürk, C. (2026). *PRML v0.1*. Zenodo. [https://doi.org/10.5281/zenodo.20177839](https://doi.org/10.5281/zenodo.20177839)
