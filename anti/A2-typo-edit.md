# Anti-pattern A2 — Editing the manifest "to fix a typo"

> **The pattern:** You spotted that `metric: "accuarcy"` should be `"accuracy"`. You fix it. The hash now mismatches every reference to the original. You shrug and update the references.

## Why it bites

The hash is the receipt. The receipt is for a specific set of bytes. **There is no "fix a typo" operation that preserves the receipt.** Any byte-level change produces a new hash, and now you have:

- The original hash (cited in places you may no longer control)
- The corrected hash (matching your fixed file)
- A confused reader who finds both and can't tell which is canonical

The fix is "issue a new manifest with a fresh `pre_registered` timestamp," not "edit and re-hash the old one."

## The temptation

Manifest YAML is human-readable. Humans see typos. The instinct is to fix them. The spec is unforgiving on this point because letting the instinct win destroys the integrity claim.

## How to spot it

Three signs you've fallen into this:

1. **You re-published a hash with the same `pre_registered` timestamp.** If two hashes share a timestamp, one of them is wrong.

2. **You edited the YAML in your model card.** Model cards are public artifacts. Editing them after publication usually means editing the manifest. If the eval team and the docs team aren't coordinated, this happens accidentally.

3. **Your CI suddenly fails the hash check on `main`.** The CI gate (Pattern 5) catches this; it's why CI gates exist.

## How to fix

**Issue a fresh manifest, with the typo fixed and a fresh timestamp:**

```yaml
prml_version: "0.1"
metric: "accuracy"   # corrected
# ...all other fields can stay the same
pre_registered: "2026-05-08T22:00:00Z"   # NEW TIMESTAMP
```

Compute a new hash. Publish both:

- The original (broken) manifest with its hash, marked publicly as "superseded by [link to corrected]"
- The corrected manifest with its new hash

If the original was anchored publicly, *do not* try to delete it from the registry. Leave it as historical record. The honest claim is: "I committed v1 at T1; I noticed a typo and committed corrected v2 at T2; the eval was run after T2."

If the eval was *already run* between T1 and the typo discovery, the question is harder: which threshold was the eval actually checked against? You may need to re-run.

## What about whitespace?

Even "fixing" trailing whitespace breaks the hash. Even adding a comment. Even pressing save in an editor that re-encodes line endings.

The reference impl `falsify lock` handles canonicalisation deterministically — that's why it exists. If you edit by hand, you have to be a robot. If you can't be a robot, use the tool.

## What about a structurally identical change?

You change `threshold: 0.92` to `threshold: 0.920`. Same number. Different bytes. **Different hash.**

YAML's flexibility is exactly what canonicalisation neutralises. The bytes are what get hashed; the *meaning* is for human readers, not the SHA-256 function.

## The honest framing

When you discover a typo in a manifest you've already committed:

- **If the manifest hasn't been anchored publicly yet:** you got lucky; fix it freely; the hash hadn't propagated.
- **If it's been anchored but no one cited it:** issue a corrected version with a fresh timestamp; mark the original superseded; the citation chain is short.
- **If it's been cited:** the typo is now part of the public record; either issue a corrected version with explicit pointer-back, or accept the typo (it's a typo, not a falsifiability flaw).

## See also

- [Pattern 7 — Revocation](../patterns/07-revocation.md) for retracting a manifest you no longer stand behind (different from a typo)
- [Anti-pattern A1 — Late hash](A1-late-hash.md) for the related sin of computing the hash after the run
