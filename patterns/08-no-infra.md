# Pattern 8 — Pre-registration without infrastructure

> **When to use:** No Python on your machine. No GitHub Action. No public registry. Just you, a YAML file, and the will to commit before the run.

## The minimum

PRML is a SHA-256 hash over canonical YAML bytes. You don't need anything we built.

```bash
# 1. Write the manifest
cat > manifest.yaml <<'EOF'
prml_version: "0.1"
metric: "accuracy"
threshold: 0.92
threshold_direction: ">="
dataset: "imagenet-1k-val"
dataset_hash: "sha256:9e2c8d1a..."
model_version: "resnet50-2026-05-08-fp16"
sample_size: 50000
seed: 42
pre_registered: "2026-05-08T20:00:00Z"
EOF

# 2. Compute the hash
sha256sum manifest.yaml
# e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  manifest.yaml

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

- **Line endings.** LF is the spec. CRLF will produce a different hash.
- **Trailing whitespace.** Strip it.
- **Tabs vs spaces.** Spaces. Two of them, indented consistently.
- **YAML quoting.** `"0.92"` (string) and `0.92` (float) are different bytes.

If you use the official reference impl (`falsify lock`), it handles canonicalisation for you. If you do it by hand, you have to be disciplined.

## What goes wrong

**1. Editing the manifest after committing the hash.** Even fixing a typo. Even adding a comment. Even pressing save in some editors that re-write the whole file. The hash will not match. The fix is not "edit and re-hash" — the fix is to issue a *new* manifest with a fresh `pre_registered` timestamp.

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
