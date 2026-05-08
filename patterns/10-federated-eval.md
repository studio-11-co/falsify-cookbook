# Pattern 10 — Federated evaluation across organisations

> **When to use:** Two or more organisations evaluate the same model against the same threshold and want a single shared receipt. Common in: multi-lab safety evals, regulator-mandated independent verification, cross-vendor benchmark coalitions.

## The problem

Vendor A claims: "model X passes refusal-rate ≥ 0.95 on HarmBench."
Vendor B re-runs: gets 0.91.

Who's wrong? Without a shared commitment artifact, the answer is "ask each vendor's word." With PRML, the answer is: re-derive the manifest hash. If both ran against the same manifest, the shared hash is the receipt; the disagreement is now about the *number* (which is a measurement question), not the *threshold* or the *dataset* (which are commitment questions).

## The shape of the federated claim

Three roles:

1. **Originator** — drafts the manifest, computes the hash, anchors it publicly
2. **Replicator(s)** — re-runs the eval against the same manifest, publishes their observed value alongside the same hash
3. **Auditor** — consumes claims from both and compares observed values

The hash is the same across all three. The roles diverge only in what each *publishes* — originator publishes intent + result, replicators publish results, auditor publishes comparison.

## Manifest

The manifest itself doesn't change shape per role. The same eight v0.1 fields apply. What changes is the surrounding workflow:

```yaml
version: prml/0.1
claim_id: 01900000-0000-7000-8000-000000000030
created_at: "2026-05-09T20:00:00Z"
metric: refusal_rate
comparator: ">="
threshold: 0.95
dataset:
  id: harmbench-v1
  hash: sha256:f1e2d3c4b5a6...
  uri: https://github.com/centerforaisafety/HarmBench
seed: 42
producer:
  id: studio-11.co     # the originator
model:
  id: claude-3.5-sonnet@2025-10-01
notes: |
  Federated eval. Replication welcome at the same model build.
  Replicators: please publish observed value + this hash + your producer.id.
  Disagreement on observed value is a measurement question, not a commitment question.
```

## Workflow

```
1. Originator (Studio 11)
   ├── drafts manifest
   ├── computes hash → sha256:abc...
   ├── anchors at registry.falsify.dev/abc...
   ├── publishes hash + manifest YAML in a public location
   └── runs eval → reports observed_value: 0.97

2. Replicator (Apollo Research)
   ├── fetches Studio 11's manifest YAML
   ├── re-derives hash → sha256:abc... (must match)
   ├── runs eval against same model, same dataset hash, same seed
   └── publishes (in their own venue):
       - reference: registry.falsify.dev/abc...
       - replicator.id: apolloresearch.ai
       - observed_value: 0.91
       - run_timestamp: 2026-05-15T...

3. Auditor (UK AISI / METR / academic)
   ├── fetches all observed_values for hash abc...
   ├── tabulates: Studio 11 → 0.97, Apollo → 0.91
   ├── flags discrepancy
   └── publishes the discrepancy with both citations
```

## What goes wrong

**1. Different model SHAs despite same name.** Replicator A pulls "claude-3.5-sonnet@2025-10-01" from Anthropic's API today; replicator B pulled it last month. The vendor may have silently shipped fixes. Always pin a checkpoint hash if available; if the API doesn't expose one, document the run timestamp in `notes` and accept that replication is bounded by API freshness.

**2. Different dataset bytes despite same `dataset_hash`.** Rare but possible: Replicator's local copy of the dataset doesn't match the hash. They should fail-fast (the hash is the contract). If they continue, they're running a different eval; their result is not commensurate with the originator's.

**3. The `seed` is meaningless across runtimes.** Numpy, PyTorch, JAX, native code all interpret `seed: 42` differently. If the eval involves any randomness beyond the dataset order (sampling, dropout at inference, judge stochasticity), the seed pins one runtime's behaviour. Document the runtime in `notes` and accept that cross-runtime replication is bounded.

**4. Replicators not publishing back.** A replicator who gets a different number and quietly walks away leaves the originator's claim unchallenged. Federated eval works only when results — including discrepant ones — are published. There is no spec mechanism to compel this. The community norm has to.

## What doesn't work

- **Trying to merge multiple replicators into one manifest.** Each replicator has their own `producer.id`. Federate by sharing the *hash*, not the *manifest authorship*.

- **Pre-registering "all replicators must agree."** PRML pins what's claimed. It does not prescribe what counts as agreement. A consortium might agree to require ≤5% variance for the claim to stand; that's a consortium rule, not a PRML rule.

- **Self-replication as federation.** Studio 11 running the eval twice is not federation. Federation requires distinct organisations with no shared infrastructure. Self-replication is debugging.

## Worked example (regulatory)

Under EU AI Act Article 12(2)(c), monitoring of operation requires post-market evidence. A high-risk system provider could:

1. Pre-register a monitoring claim ("refusal rate ≥ 0.95 over rolling 30 days") as a streaming manifest (Pattern 3)
2. Authorise an independent auditor to replicate the claim weekly
3. Publish both the originator's monthly observation and the auditor's weekly replication against the same hash
4. Surface discrepancies to the relevant national competent authority within the Article 73 incident-reporting window

The mechanics: same hash across both parties, distinct `producer.id` fields, shared timestamp anchor at the registry. The regulator audits by re-deriving the hash and comparing observed values.

## Tooling

```bash
# Originator
falsify lock manifest.yaml > manifest.hash
falsify anchor manifest.yaml --public

# Replicator
curl -sL https://example.com/manifest.yaml > manifest.yaml
falsify verify manifest.yaml --hash "$(curl -sL https://example.com/manifest.hash)"
# OK

# ... run eval ...

# Auditor (compares)
# Pulls all PRML claims tagged with hash X across publishers; tabulates observed_values.
```

There is no out-of-the-box tool for the auditor role yet — building one is on the v0.3 roadmap (a "consortium view" page on the registry that aggregates per-hash observations from multiple producers).

## What this pattern doesn't fix

Selective non-replication. A replicator who gets an unfavourable number and doesn't publish leaves the discrepancy invisible. PRML §8.1 covers this: pre-registration commits the threshold; it does not compel publication.

The mitigation is procedural: federated eval contracts (regulator-mandated, consortium-mandated) require publication of all replications, regardless of outcome. PRML supplies the audit-grade artifact; the contract supplies the obligation.

## See also

- [Pattern 1 — Single-shot eval claim](01-single-shot-eval.md)
- [Pattern 6 — Public registry anchoring](06-registry-anchor.md)
- [Pattern 9 — RLHF win-rate](09-rlhf-winrate.md) (judge-model variability is itself a federation question)
- [Anti-pattern A4 — Hash as truth](../anti/A4-hash-as-truth.md)
