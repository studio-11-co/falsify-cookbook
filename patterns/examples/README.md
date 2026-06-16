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

Real: PRML canonicalisation/hashing/verdicts (`falsify_prml`). Sample-modelled: a faithful
in-file lm-eval results dict so it runs with no lm-eval install; `--results` accepts a real one.
