# Pattern 6 — Public registry anchoring

> **When to use:** You want the world (or at least a search engine) to find your manifest hash without you having to host anything.

## What the registry does

`registry.falsify.dev` accepts a manifest, returns:

- A SHA-256 receipt
- A permalink (`registry.falsify.dev/<hash>`)
- A README badge SVG snippet
- A "verify in browser" page

It does **not**:

- Store your manifest content beyond the hash + a few metadata bytes
- Require an account
- Require email
- Maintain server-side state about you

A registry anchor is just: "this hash existed at this timestamp, witnessed by this server."

## Anchor flow

```bash
# Generate the manifest and lock it
falsify lock manifest.yaml > manifest.hash

# Anchor (single command)
falsify anchor manifest.yaml --public
# Anchored at https://registry.falsify.dev/abcdef0123...
# Badge:
# [![PRML](https://registry.falsify.dev/badge/abcdef0123...)](https://registry.falsify.dev/abcdef0123...)
```

Drop the badge in your README, paper, or model card.

## When to anchor publicly

**Anchor publicly when:**

- The eval claim will be cited in a paper or model card
- The eval is part of a model release that competitors will reference
- The publisher (you) wants to be on record for an external audit later
- The deadline pressure is real and you want a third-party witness to the timing

**Don't anchor publicly when:**

- The manifest contains references to private datasets, internal model versions, or trade-secret thresholds
- You're still iterating on the eval design (your hash will change, leaving orphan anchors)
- You're working under NDA and the claim itself is confidential
- The eval is for internal QA only (no external audit need)

## Anchor without publishing

You can anchor *privately* — compute the hash, sign it, store it in your own internal git repo, and skip the public registry entirely. Pattern 8 (no-infra) shows the workflow. The registry is convenience; pre-registration works without it.

## What goes wrong

**1. Anchoring before you're ready.** You anchor today, find a typo tomorrow, fix the YAML, anchor again. Now there are two manifests and the public can't tell which one is canonical. Fix: only anchor once you've reviewed.

**2. Forgetting the manifest content survives the hash.** The registry stores `(hash, timestamp, optional metadata)`. The *manifest YAML itself* is your responsibility to publish. If you anchor a hash and never publish the manifest, no one can verify what you committed to.

**3. Anchoring private data.** If your manifest contains `internal_threshold: 0.6_secret`, that field is reproducible by anyone who has the manifest. If the manifest is in a public PR, the world knows. Don't put confidential thresholds in a public manifest.

**4. Trusting a single registry.** The registry is one witness. For higher integrity, anchor the same hash to multiple witnesses:

- `registry.falsify.dev`
- An OpenTimestamps stamp (Bitcoin-anchored)
- A git commit on a public repo
- A tweet

Each adds an independent timestamp claim. Three witnesses are harder to coordinate-lie about than one.

## What doesn't work

- **Treating the registry as authoritative.** The registry is a witness. The math is authoritative. If the registry disappears tomorrow, anyone with the manifest YAML can re-derive the hash with `falsify verify`.

- **Using the registry for reading model performance.** The registry stores hashes; it doesn't store your eval scores. Publish your scores in your model card or paper; the registry tells the reader the threshold was committed before you wrote them down.

- **Privacy through obscurity.** Anchoring a hash of a private manifest doesn't make the manifest secret. It commits you to a content you might later reveal. If you anchor and reveal, the reveal must match the hash. If you anchor and never reveal, the anchor is meaningless to outsiders.

## Revocation

If you need to revoke: see [Pattern 7 — Revocation](07-revocation.md).

## Next pattern

If you want to revoke a published manifest: see [Pattern 7](07-revocation.md).
