# Anti-pattern A4 — Treating the hash as proof of *truth*

> **The pattern:** You see a PRML hash on a model card. You assume the score is correct, the eval was rigorous, the publisher honest, and the threshold reasonable.

## Why it bites

The hash proves **commitment**. It does not prove:

- That the eval was actually run (the publisher could have made up the score)
- That the dataset was actually used (the publisher could have run a different one)
- That the threshold is reasonable (the publisher chose it)
- That the model is good (the score is just a number)
- That the publisher is honest

This is the most important property of PRML for outsiders to internalise. The spec is precise about it. §8.1 spells it out. Marketing tends to round off.

## What the hash actually says

If you compute the SHA-256 of `manifest.yaml` and get hash `H`, and `H` matches the value cited in a paper, you have learned exactly one thing:

> **At some point**, the publisher had a manifest YAML whose bytes hashed to `H`.

You have not learned:

- *When* they had it (the timestamp anchor adds that)
- *Why* the threshold is what it is
- *Whether* the eval was honestly run against the committed threshold
- *Whether* the score reported alongside is accurate

You have an audit hook, not a proof.

## What it adds despite the limit

The hash is still valuable. With it:

- A publisher who *wants* to be honest has a clean way to demonstrate it (commit publicly, then run, then publish; the chain is verifiable)
- A publisher who *intends* to lie has to commit to a false threshold *before* the data — which is harder than retrospective rationalisation
- A community auditor can check claims efficiently — re-deriving a hash takes seconds; auditing a paper takes weeks
- A regulator can require that public claims include a hash — and then enforce on the *commitment*, not the *truth*

The hash narrows the set of lies that are easy. It does not eliminate the set of lies that are hard.

## The trust chain remains

Even with PRML, trust ultimately rests on:

1. **The publisher's claim that they ran the eval honestly.** No serialisation primitive can verify this from outside.
2. **The community's ability to spot inconsistencies.** PRML makes some inconsistencies cheap to detect (threshold tampering, dataset version drift). It doesn't make all inconsistencies cheap.
3. **Independent re-evaluation.** The strongest verification is a second team running the eval and producing matching scores. PRML supports this by pinning enough metadata to make re-runs reproducible.

If you treat the hash as the only check, the trust chain is "the publisher committed a claim before the data" — which is much weaker than "the claim is true."

## How to read a PRML hash skeptically

When you see a hash on a model card or paper:

1. **Re-derive it locally.** `falsify verify manifest.yaml --hash H`. If it doesn't match, the manifest was edited; stop.
2. **Check the timestamp anchor.** Was the hash anchored *before* the paper's submission date? If not, pre-registration is unverified.
3. **Read the manifest.** Does the threshold direction match the score? Is `dataset_hash` traceable to a real, accessible dataset?
4. **Check that the score is consistent with the threshold.** A 0.95 score with `threshold: 0.92` and direction `>=` makes sense. A 0.50 score with the same fields means either the publisher reported something the threshold says is a failure (which is honest!), or the manifest was decoupled from the run.
5. **Don't treat any of this as the final word.** It's a small primitive. It is not a substitute for community re-evaluation.

## A worked example

Imagine a paper claims: "Our model achieves 0.94 mean reward on LunarLander-v2, threshold ≥ 0.90, hash `sha256:abc...`."

The hash matches the manifest. Great. What you now know:

- The paper authors had a manifest committing to threshold 0.90 in direction `>=`, against LunarLander-v2 with the documented dataset hash, with the documented seeds, at the documented pre-registration timestamp.

What you don't know:

- Whether the score 0.94 is real, fabricated, or computed against a different rollout
- Whether they ran 100 seeds and only published the top 5
- Whether the model in `model_version` is the *same* model that was actually evaluated
- Whether the aggregation method matches what they describe in prose

To know any of those things, you need methods *outside* PRML — replication, code release, external audit, regulatory inspection.

## The right disposition

Read PRML hashes as you would read pre-registration in clinical trials: as a small, sharp tool that catches one specific kind of dishonesty (post-hoc threshold tuning) and is silent on every other kind. A high-rigor evaluation ecosystem combines PRML with reproducible code, dataset transparency, independent re-runs, and human auditing. PRML is one node in that web, not the web itself.

## See also

- PRML v0.1 §8.1 — the spec's own statement of limitations
- [Pattern 6 — Public registry anchoring](../patterns/06-registry-anchor.md) for the timestamp-anchor question
- [Anti-pattern A1 — Late hash](A1-late-hash.md) for one specific way the chain can be quietly broken
