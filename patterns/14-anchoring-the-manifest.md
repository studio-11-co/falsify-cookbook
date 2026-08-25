---
Authors: Cüneyt Öztürk (falsify)
License: CC0-1.0
---

# Pattern 14 — Where you put the manifest decides what it proves

> **When to use:** You already write the criteria down before the run. Someone outside
> your organisation now has to believe the file existed before the scores did, and you
> want to know what each storage choice actually establishes for them.

A manifest written by the job it constrains proves that the run was self-consistent.
It does not, on its own, prove ordering. What supplies the ordering is where you put it.

This pattern is about that choice. It is deliberately not about any one manifest format —
PRML is used in the examples because it is what these docs are about, but every line below
holds for a plain JSON file with a SHA-256 next to it.

## The question each anchor answers

| Anchor | Who has to be trusted | What it establishes |
|---|---|---|
| Commit to your own repository | you | the file's **content**, and that it is in your history |
| Signed CI attestation | your CI provider | the file existed when a **build you did not fully control** ran |
| Independent timestamp or transparency log | a third party, or nobody | the digest existed **before a time you did not choose** |

None of these is wrong. They answer different questions, and the right one depends on who
is going to read the record.

## Anchor A — commit it (do this regardless)

Committing the criteria file is the cheapest thing you can do and you should do it. It
gives you the content, the diff history, and a place for review to happen.

What it does not give a reader outside your organisation is the ordering, because the
dates in a commit are supplied by whoever makes the commit:

```console
$ echo "threshold: 0.9" > criteria.yaml && git add criteria.yaml

$ GIT_AUTHOR_DATE="2020-01-01T00:00:00Z" \
  GIT_COMMITTER_DATE="2020-01-01T00:00:00Z" \
  git commit -m "criteria"

$ git log -1 --format='author %ad  committer %cd' --date=iso
author 2020-01-01 00:00:00 +0000  committer 2020-01-01 00:00:00 +0000
```

That commit was made today. Both dates are environment variables.

Note that **both** have to be set. Setting only `GIT_COMMITTER_DATE` leaves the author date
showing the real time, which is what gives most casual backdating away:

```console
$ GIT_COMMITTER_DATE="2019-06-06T00:00:00Z" git commit -m "second"
$ git log -1 --format='author %ad  committer %cd' --date=iso
author 2026-08-24 16:53:31 +0300  committer 2019-06-06 00:00:00 +0000
```

So a commit is evidence to a colleague, who can see the review that happened around it,
and much weaker evidence to a regulator, a customer or a journalist, who cannot.

This is not an argument against committing. It is an argument about what the commit proves
to someone who was not in the room.

**When Anchor A is the whole answer.** Treating the chain of commits as the audit trail is
mainstream practice, and for a large class of readers it is the right answer. Anthropic's
*AI-Native SDLC playbook* (21 August 2026) does exactly this for regulated engineering
teams: the evidence for a change is the committed intent file, carrying its author, its
timestamp and its full revision history, and the chain of commits is the audit trail of who
asked for what and who approved it. That is sufficient there, and the reason is worth
naming. The reader is inside the organisation, or has access to the repository and to the
people who wrote it, so they can see the review that happened around the commit and judge
whether the dates are plausible. The gap this pattern is about opens only when the reader
has neither.

## Anchor B — a signed CI attestation (if you already produce one)

If your pipeline already emits a signed build attestation — SLSA provenance, an in-toto
statement, a signed release artifact — put the manifest digest in it and stop here. It is
materially stronger than a commit: the timestamp comes from infrastructure you do not
fully control, and the signature makes tampering detectable rather than invisible.

What it still assumes is that the CI provider's clock and signing key are outside the
reach of the party publishing the result. For most teams that is a reasonable assumption.
For a claim that a competitor or a regulator will read adversarially, it is worth stating
out loud rather than leaving implicit.

## Anchor C — an independent timestamp

This is the case the first two do not cover: a reader who has no relationship with you,
no access to your CI, and no reason to take your word for the clock.

An RFC 3161 timestamp authority countersigns a digest and returns a token. Verification
needs the token, the digest, and the authority's certificate — not you, and not your
infrastructure:

```console
$ openssl ts -verify -digest <sha256> -in receipt.tsr -CAfile tsa-chain.pem
Verification: OK
```

A public transparency log adds a second property: the entry is append-only and mirrored,
so its absence later is itself evidence. Sigstore's Rekor is the usual choice.

**What this costs, stated plainly.** You are adding a network call at lock time and a
dependency on a service being reachable. If the authority is down, you either block the
run or fall back to Anchor A and record that you did. Decide which before it happens,
not during.

**What it does not give you.** A timestamp proves a digest existed by a time. It says
nothing about whether the criteria were sensible, whether the test set was representative,
or whether the result is correct. Those stay exactly where they were.

## Choosing

- Publishing internally, read by colleagues → **A**, and spend the effort on review instead.
- Shipping under a contract or a framework that asks for dated records → **B**.
- The number will be read by someone with no reason to trust you → **C**, with **A** underneath it.

The common mistake is to reach for **C** first because it is the most technical, when the
reader was always going to be a colleague. The other mistake is to assume **A** carries
weight it does not, which is the one this pattern exists to name.

## Limits

- All three anchor a **digest**, not a decision. Nothing here makes a threshold appropriate.
- Anchoring after the results are known produces a valid token and a worthless claim. The
  ordering is the whole point, so the lock belongs before the run in the same script, not
  in a cleanup step afterwards.
- If the manifest is regenerated by the same job that reads it, the digest will always
  match and will have proved nothing. Lock once, read many times.
