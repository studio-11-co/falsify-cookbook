# Pattern 7 — Revocation

> **When to use:** A pre-registered manifest needs to be retracted because the underlying dataset is found contaminated, the model build is recalled, or the claim is no longer accurate.

> **Spec status:** Revocation is a **v0.2 feature** ([proposal P-03](https://spec.falsify.dev/v0.2-rfc#p-03-revocation-primitive)). For v0.1-only deployments, the equivalent is a public retraction notice — see "v0.1 fallback" below.

## What revocation is — and isn't

**Revocation is not "the manifest is wrong."** A manifest is just bytes. Bytes don't have correctness; they have hashes. If the hash matches, the manifest *was committed* — full stop.

**Revocation is "the *claim* is no longer one I stand behind."** The hash still verifies. The publisher is signaling: "I used to vouch for this commitment. I no longer do."

Three things must be true for revocation to be meaningful:

1. The hash must continue to verify (the bytes don't change)
2. The revocation must be **timestamped** (it happened at a specific time)
3. The revocation must be **discoverable** (someone trying to verify the manifest sees the revocation alongside)

## How to revoke

In v0.2, you add two optional fields to the manifest itself:

```yaml
prml_version: "0.2"
# ...all the original fields, unchanged...
revoked_at: "2026-05-15T10:00:00Z"
revocation_reason: "dataset_compromised"
```

Then re-publish the manifest with those fields added. The hash now changes (because the bytes changed), but you publish *both* hashes:

- The original hash (committed at `pre_registered`)
- The revocation hash (committed at `revoked_at`)

The registry pairs them: when someone visits the original permalink, the page shows both states.

## v0.1 fallback (no spec-level revocation)

If you must use v0.1, revoke out-of-band:

1. Publish a public retraction notice (your blog, a tweet, a git commit in a public repo)
2. Reference the original hash explicitly
3. State the reason and the timestamp
4. Don't edit the original manifest YAML — the original commitment stays intact

This isn't worse than v0.2 revocation; it's just less mechanically discoverable. If your eval ecosystem has a community norm (Hacker News announcement, Hugging Face model card update), use it.

## Revocation reason vocabulary

v0.2 P-03 proposes a controlled vocabulary:

| Reason | When to use |
|---|---|
| `dataset_compromised` | The eval set is found contaminated, leaked, or otherwise unfit for the original claim |
| `model_recalled` | The model build referenced in `model_version` is no longer publicly available or has been withdrawn |
| `author_request` | Voluntary withdrawal for non-emergency reasons (e.g., a typo discovered post-anchor) |
| `other` | Catch-all; should accompany a free-form note in the publication, not the YAML |

Pick the most accurate one. Don't use `author_request` to hide a `dataset_compromised` event. The voluntary register is for low-stakes corrections; the others are for integrity-bearing events.

## What goes wrong

**1. Revoking quietly.** A revocation that no one sees is no revocation. After you revoke, push the change to all places the original hash was cited (model card, registry, paper appendix, awesome-list entries).

**2. Revoking a hash that's already been used as a citation.** Papers cite hashes in BibTeX. If you revoke after publication, you cannot un-cite. The honest move: publish an erratum that names the revocation, leave the citation intact, and trust readers to follow the chain.

**3. Frequent revocations.** A publisher who revokes every other manifest erodes the trust the spec is supposed to bootstrap. Pre-registration assumes you commit when ready, not when convenient. If you find yourself revoking often, the underlying eval design is flawed; fix that, not the manifest.

**4. Revocation as silent retraction.** Don't use revocation as a way to walk back claims that were embarrassing for non-integrity reasons. "We were wrong about the threshold direction" is not a revocation; it's a publication mistake. Issue a corrected manifest with a fresh `pre_registered` timestamp.

## What doesn't work

- **Editing the original manifest in place.** Even with `revoked_at`, the *spirit* of pre-registration is that the original bytes stay readable. v0.2 supports adding revocation fields; it does not support deleting other fields.

- **Revoking by deleting the manifest from the registry.** Registries are witnesses, not gatekeepers. Deleting from one registry doesn't delete the hash; deleting from all registries doesn't unmake the hash. The hash exists once you compute it.

- **Treating revocation as a blame-shifting tool.** A published revocation says "I commit this is no longer my claim." It doesn't say "this was never my fault." Own the revocation.

## Tooling

```bash
# v0.2 (when shipped)
falsify revoke manifest.yaml --reason dataset_compromised
# Adds revoked_at + revocation_reason, recomputes hash, prints both

# v0.1 (now)
# Publish a retraction notice manually; reference the hash; never edit the manifest.
```

## Next pattern

If you want a workflow with no infrastructure at all: see [Pattern 8 — Pre-registration without infrastructure](08-no-infra.md).
