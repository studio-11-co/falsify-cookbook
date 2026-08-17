# Pattern 8 — Pre-registration without infrastructure

> **When to use:** No Python on your machine. No GitHub Action. No public registry. Just you, a YAML file, and the will to commit before the run.

## The minimum

PRML is a SHA-256 hash over canonical YAML bytes. You don't need anything we built.

The one thing you have to get right: **write the file in canonical form.** `sha256sum`
hashes the bytes on disk, so those bytes must already be the canonical bytes, or your
hash will not match the one the reference CLI, the registry, or any other verifier
derives from the same manifest. Canonical form is: keys sorted alphabetically at every
level, minimal quoting, two-space indent, LF endings, one trailing newline. The
manifest below is already canonical — that is why the field order looks alphabetical
rather than logical.

```bash
# 1. Write the manifest — in canonical form (keys sorted, minimal quoting)
cat > manifest.yaml <<'EOF'
claim_id: 01900000-0000-7000-8000-000000000005
comparator: '>='
created_at: '2026-05-08T20:00:00Z'
dataset:
  hash: 9e2c8d1a3b4c5d6e7f80911a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e
  id: imagenet-1k-val
metric: accuracy
producer:
  id: your-lab.dev
seed: 42
threshold: 0.92
version: prml/0.1
EOF

# 2. Compute the hash
sha256sum manifest.yaml
# 5eb01a04a4cfd109c857c724b2a761d2f5f25c71ad5627499562211c7d9292eb  manifest.yaml

# 3. Commit the hash somewhere public-and-timestamped (your choice)
#    - tweet it
#    - paste it in a public Slack
#    - email it to yourself with the eval threshold in the subject
#    - git commit it in any public repo

# 4. Run the eval

# 5. Later: re-derive
sha256sum manifest.yaml
# Should match step 2. If not, the file was edited.
```

## Why this is enough

The only requirements for pre-registration are:

1. **A canonical input** — the manifest YAML
2. **A deterministic function** — SHA-256
3. **A timestamp anchor** — anything with a verifiable time order

Step 3 is the hidden one. Most people skip step 3 and then can't prove *when* they committed. Don't skip it. Pick anything that has a verifiable timestamp:

- **Git commit on a public repo.** Free; everyone has it; git's commit timestamp is independently verifiable.
- **A tweet.** Platform-dependent, but timestamped and indexed by archive.org within minutes.
- **OpenTimestamps.** Bitcoin-anchored timestamps, free, no account.
- **Your registrar's DNS TXT record.** If you run a domain.

## Canonicalisation gotchas

The hash depends on the exact bytes. The bytes depend on:

- **Key order.** Canonical form sorts keys alphabetically at every level, including
  inside `dataset` and `producer`. A "logical" order hashes differently. This is the
  one people miss, because the file still looks perfectly valid.
- **Line endings.** LF is the spec. CRLF will produce a different hash.
- **Trailing whitespace.** Strip it. Keep exactly one newline at the end of the file.
- **Tabs vs spaces.** Spaces. Two of them, indented consistently.
- **YAML quoting.** `"0.92"` (string) and `0.92` (float) are different bytes. Canonical
  form quotes only what YAML would otherwise misread — `'>='` and the timestamp here.

If you use the official reference impl (`falsify lock`), it handles canonicalisation for you. If you do it by hand, you have to be disciplined.

## What goes wrong

**1. Editing the manifest after committing the hash.** Even fixing a typo. Even adding a comment. Even pressing save in some editors that re-write the whole file. The hash will not match. The fix is not "edit and re-hash" — the fix is to issue a *new* manifest with a fresh `created_at` timestamp.

**2. Inconsistent line endings between machines.** You hash on macOS (LF), someone re-derives on Windows (CRLF), the hash doesn't match. Pin LF in your `.gitattributes`:

```
*.yaml text eol=lf
```

**3. Posting the manifest content but not the hash.** Anyone who finds your manifest later can run `sha256sum` themselves, but they can't prove that hash was the one *you* meant. The public step is the *hash*, not the manifest.

## What doesn't work

- **Trusting your filesystem mtime.** A file's modification time is not a commitment to anyone. Filesystem timestamps are user-editable.

- **A private timestamp.** "I sent it to myself by email at 8 PM" is hard to verify after the fact. Pick a *public* anchor.

- **Skipping the manifest itself.** If you only commit a hash, no one (including you) can verify the manifest you intended. Always commit the manifest content alongside the hash.

## When to graduate

If you're committing more than ~five manifests per month, the no-infra workflow becomes a chore. At that point, install the reference CLI:

```bash
pip install falsify
```

It does steps 1–3 in one shell pipeline and handles canonicalisation correctly across platforms.

## Next pattern

If you want CI-level enforcement: see [Pattern 5 — CI gate](05-ci-gate.md).
