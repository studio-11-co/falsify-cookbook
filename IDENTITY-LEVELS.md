# PRML identity levels

> **What this document is.** A non-normative ladder for the strength of
> the binding between a PRML manifest's `producer` claim and the real-world
> entity that authored it. Five levels, from "you just typed your name into
> a YAML file" to "your manifest is anchored in a public transparency log
> tied to an institutional identity." Each level is auditable; they differ
> in how much trust the verifier must extend to the producer.
>
> **What this document is not.** Normative. PRML v0.1 and v0.2 accept any
> identity level; the spec does not refuse a manifest because its producer
> is unsigned. This document exists so that a verifier evaluating a
> manifest can place it on the ladder and decide accordingly, and so that
> producers can decide how high to climb. The v0.3 RFC track will lift
> these levels into a normative `identity_level` field.

## The five levels

### Level 0 — Unsigned local manifest

The producer typed their name (or institution, or GitHub handle) into the
`producer` field. The manifest is hashed and may be stored locally or
shared. Nothing externally observable ties the producer string to the
hash beyond the bytes themselves.

```yaml
producer:
  id: alice@example.com
```

**What this defends against:** A producer who keeps the manifest private
cannot retroactively edit it without changing the hash. Useful for
personal experiments and for hashing-as-discipline; useful inside an
organization where the audience is colleagues.

**What this does not defend against:** Anyone holding the manifest can
swap the `producer` field, re-hash, and publish under a different name.
The original "alice" identity claim has no anchor.

**Use when:** You are pre-registering for yourself or your immediate
team and external verification is not in scope.

---

### Level 1 — Public git commit or registry timestamp

The manifest is committed to a public git repository, or POSTed to a
public PRML registry. Either action records a server-side wall-clock
timestamp and an immutable content-addressed receipt outside the
producer's control.

```yaml
producer:
  id: falsify.dev
# anchor: git commit a3f9c...c821 in studio-11-co/falsify on 2026-05-08
# or:   registry receipt at registry.falsify.dev/<hash>
```

**What this defends against:** Producer cannot back-date the manifest to
a time before the commit/registry observation. The hash is mirrored in
at least one external system.

**What this does not defend against:** The `producer` string is still
unsigned. Anyone with push access to the repository, or anyone with a
manifest copy, can submit it under their own name elsewhere. Multiple
"falsify.dev" producers are not distinguishable.

**Use when:** You publish your manifests in a public repo and want a
default audit trail. This is the level most v0.1/v0.2 manifests
operate at in practice.

---

### Level 2 — Signed commit or detached PGP / minisign signature

The manifest carries a cryptographic signature over the canonical bytes,
produced with a key whose public half is documented out-of-band (PGP
key on the producer's website, minisign key in a `MAINTAINERS` file,
git commit signed with a known SSH key).

```yaml
producer:
  id: falsify.dev
  signature: <detached signature over canonical bytes>
```

**What this defends against:** A different party cannot republish under
the same `producer.id` without the corresponding private key. The
binding between producer string and signing key is verifiable, as
strongly as the out-of-band key publication is verifiable.

**What this does not defend against:** Key compromise. Key rotation
mechanics. Producer identity is exactly as strong as the producer's
key-management hygiene. There is no central revocation channel.

**Use when:** You operate under an established public identity (an
open-source project with a published key, an institution with a
documented signing process) and want signature-strength binding without
external dependencies.

---

### Level 3 — Sigstore + Rekor transparency log

The manifest is signed via Sigstore's keyless flow (`cosign sign-blob`),
producing a short-lived certificate from Fulcio bound to an OIDC
identity (GitHub Actions, Google, Microsoft, GitHub user) and a Rekor
log entry. Both certificate and Rekor entry are public.

```yaml
producer:
  id: falsify.dev
  sigstore_bundle: <inline JSON bundle>
# Rekor entry: https://search.sigstore.dev/?hash=<sha256>
```

**What this defends against:** Producer identity is bound to an
authoritative OIDC issuer (the org that runs your GitHub repo, or your
Google account), not to a manually-maintained key. Rekor entries are
append-only and publicly mirrored; a producer cannot delete a signature
post-hoc. The timestamp on the Rekor entry is wall-clock-authoritative.

**What this does not defend against:** Compromise of the underlying
OIDC account. Cookbook Pattern 11 walks through the full Sigstore flow
including CI-based signing.

**Use when:** You want the strongest available open identity binding
without running your own PKI. This is the recommended default for
production audit trails.

---

### Level 4 — Institutional / regulated identity

The manifest is signed by an institutional key managed under a
documented policy (eIDAS qualified certificate, FIPS 140-3 validated
HSM, journal-issued submission credential, notified body assessment
credential), and the identity binding is enforced by a registry that
refuses lower-level submissions.

```yaml
producer:
  id: hospital.example.org
  signature: <signature from institutional HSM>
  key_id: sha256:<HSM-bound key fingerprint>
# anchor: institutional registry entry, regulator-mirrored
```

**What this defends against:** Regulatory and journal-grade scenarios
where the producer must be tied to a legally-identifiable entity, key
management is auditable under a published policy, and the registry
itself is part of the trust chain.

**What this does not defend against:** Institutional policy failures
(an institution that signs everything its employees produce without
review). Higher levels of trust place higher demands on the
institution's internal process; PRML cannot verify those.

**Use when:** Your manifest is part of a clinical-trial submission, a
notified-body conformity assessment, a peer-reviewed publication with
mandatory pre-registration, or any other context where the registry
itself is operated by a trusted institution.

---

## How to decide

A producer choosing a level should ask:

1. **Will the verifier know me out-of-band?** If yes, Level 0–1 may be
   enough. If no, you need Level 2 or higher.
2. **Is the cost of mis-identification borne by me or by a third party?**
   Internal experiments: Level 0 fine. Public claims: Level 1 default.
   Regulated claims: Level 3+.
3. **Can I run the higher-level mechanism reliably?** Level 3 needs OIDC
   plus a CI runner with `cosign`. Level 4 needs institutional support.
   Climbing levels you cannot maintain consistently is worse than
   sitting at a level you can.

A verifier evaluating a manifest should ask:

1. **What level does this manifest claim?** (Look for signatures,
   Sigstore bundles, registry anchors.)
2. **What level can I independently confirm?** (Re-derive the hash;
   check Rekor; check git commit signatures.)
3. **What level does my use case require?** (A blog post: Level 1 is
   often enough. An audit submission: Level 3+ is the floor.)

## What changes in v0.3

The v0.3 RFC track proposes a normative `identity_level` field with
values 0–4 matching this document. The field would be informative
(self-declared); verifiers retain the obligation to independently
confirm the level. See `spec/v0.3-backlog/02-producer-struct.md`.

## Related

- v0.1 §2.3.3 — `producer` field semantics (existing signature field)
- v0.1 §8.1 — threat model
- Cookbook Pattern 11 — PRML + Sigstore for execution integrity
- v0.3 backlog item 02 — structured producer field
