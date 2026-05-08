# Anti-pattern A1 — Computing the hash *after* the run

> **The pattern:** You finish the eval. You like the score. You write the YAML manifest. You compute the hash. You publish.

## Why it bites

Pre-registration is not "having a YAML file." Pre-registration is **the threshold being committed before the data arrives**. If you compute the hash after the run, you have a YAML file. You do not have pre-registration.

The hash, computed late, is indistinguishable mechanically from a hash computed early. The whole spec exists because **mechanical indistinguishability is the point**: a third party verifying your hash cannot tell whether you committed early or late.

So the integrity of late-hashing is purely an *internal* commitment. If your audit chain is "trust me," PRML adds nothing. If your audit chain is "verifiable by anyone," PRML adds nothing *if* you compute the hash late.

## How to spot it

Two telltale signs:

1. **Your `pre_registered` timestamp is suspiciously close to your eval completion timestamp.** A pre-registration timestamp 6 hours before a 5-hour eval looks fine on the surface. A pre-registration timestamp 3 minutes before is suspicious.

2. **Your manifest references the *exact* score you got.** If `value: 0.9237` is the last decimal of the actual mean, you wrote that *after* the run. If `value: null` and the score is reported separately, the manifest commits to the threshold, not the answer.

## How to fix

**Make pre-registration the first step, not the last.** Concretely:

1. Write the manifest with `value: null` and a `threshold` you commit to in advance
2. Compute the hash
3. Anchor the hash publicly (or commit it to a public git repo)
4. *Then* run the eval
5. *Then* publish the score alongside the (already-anchored) hash

Step 3 is the one most often skipped. Without a public timestamp on the hash, you can claim any pre-registration time you want — and a third party cannot disprove it. The public anchor is what makes the timestamp falsifiable.

## A counter-example to the counter-example

There is one legitimate case for late-hashing: **emulating pre-registration retroactively for a historical eval**. If you ran an eval in March and want to publish the manifest now, you write the manifest, compute the hash, and label `pre_registered` as the *original* run date — but you **must** disclose that the manifest was written after the run. The honest pattern is:

```yaml
prml_version: "0.1"
# ...
pre_registered: "2026-03-01T00:00:00Z"
# meta-note (not a spec field, just a YAML comment for readers):
# this manifest was authored 2026-05-08 from the eval logs;
# the threshold above was the working threshold during the original run,
# documented in commit abc123 of the eval repo on 2026-02-28.
```

This isn't pre-registration. It's *retrospective documentation*. Don't pretend it's the same thing.

## The framing rule

When in doubt: **the hash is a commitment to a threshold, not a record of a result.** If you wrote the threshold *after* knowing the result, the hash records nothing useful.

## See also

- [Pattern 1 — Single-shot eval](../patterns/01-single-shot-eval.md) for the proper workflow
- [Pattern 6 — Public registry anchoring](../patterns/06-registry-anchor.md) for making timestamps verifiable
