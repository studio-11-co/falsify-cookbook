# Example: a pre-committed eval claim as record zero of a runtime trail

> Pattern 1 + 6, for runtime audit trails. One file, one dependency.

## What this shows

A runtime trail records what an agent or pipeline did. It does not, by itself, show that the bar a result was judged against is the bar that was agreed before the run. If someone edits the threshold after a weak result, a check that reads the current threshold still says **PASS**.

This example writes a PRML claim (metric, comparator, threshold, dataset hash, seed) as **record zero** of a generic evidence trail, then checks every later verdict against it:

| Case | Trail-only check | Anchored check |
|---|---|---|
| 1. Honest pass (0.97 against ≥ 0.95) | PASS | PASS |
| 2. Honest fail (0.93 against ≥ 0.95) | FAIL | FAIL |
| 3. Goalpost moved (threshold edited to 0.90 after the 0.93 result) | **PASS** | **TAMPERED** |

## Run it

```bash
pip install falsify
python3 trail_anchor.py
```

## Fitting it to your trail

Record zero needs two fields your trail can already store: the PRML manifest hash and the claim itself. The anchored check is a re-hash of the claim in use, compared with record zero, before the comparison. To make the anchor checkable by someone who does not trust the trail, also commit the manifest to a public registry or timestamp it (see [Pattern 6](../../patterns/06-registry-anchor.md) and [Pattern 14](../../patterns/14-anchoring-the-manifest.md)).

## What it does not show

The anchor shows that the claim in use is, or is not, the claim hashed in record zero. It does not show that the run happened after the claim was written, and it does not show that the observed value is correct.
