# Pattern 13 — runnable composition

`pattern13_prml_commit_reveal.py` makes the co-authored Pattern 13 executable end to end:
PRML pre-registration + a valichord_attestation-style bundle + a local commit-reveal round,
then three adversarial cases showing each layer catches what the others can't.

```
python3 pattern13_prml_commit_reveal.py
```

Honesty: the PRML layer uses the real `falsify_prml` reference; the bundle hashing
(Merkle root, bundle_hash/content_hash) is real crypto matching the v1.2 format; the
commit-reveal is real crypto but simulated locally (production ValiChord runs on
Holochain across isolated nodes). No network, stdlib only.

## lm-eval ↔ PRML bridge

`lm_eval_to_prml.py` turns an lm-evaluation-harness run into a pre-registered PRML claim,
the honest way: **lock the bar from the task config BEFORE the run, verify the observed
metric from `results.json` AFTER**. Avoids the "hash after the run" anti-pattern (anti/A1).

```
python3 lm_eval_to_prml.py                                   # built-in demo
python3 lm_eval_to_prml.py --mode lock --results results.json \
        --task hellaswag --metric acc_norm --threshold 0.75  # real run
```

Real: PRML canonicalisation/hashing/verdicts (`falsify_prml` — the same reference the spec and the
4 byte-equivalent impls use, no parallel schema). Sample-modelled: a faithful in-file lm-eval results
dict so it runs with no lm-eval install; `--results` accepts a real one.

**This is the flagship reference integration** — what it looks like to drop a pre-committed eval claim
into a tool a platform already uses (lm-evaluation-harness, the most-used LLM harness). The demo's
`[ATTEST]` step emits the locked claim as an **in-toto / ITE-6 Statement** (`falsify >= 0.3.8`), so a
host that already ingests SLSA/in-toto can treat a pre-registered eval as one more predicate type — the
3-function embed path is in [`docs/EMBED.md`](https://github.com/studio-11-co/falsify/blob/main/docs/EMBED.md).
Related upstream thread: [lm-evaluation-harness PR #3752](https://github.com/EleutherAI/lm-evaluation-harness/pull/3752).
