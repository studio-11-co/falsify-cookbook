# Pattern 5 — CI gate via `prml-verify-action`

> **When to use:** You publish models from a Git repository, evaluation thresholds live in committed YAML, and you want PRs that ship a model with a tampered eval claim to be automatically blocked.

## The shape

A PRML manifest sits in your repo at `eval/manifest.yaml`. The published claim's hash sits next to it at `eval/manifest.hash`. A GitHub Action runs on every PR and:

- exit 0 → the manifest YAML and the recorded hash agree (PR proceeds)
- exit 10 → the eval threshold was violated (PR proceeds with a flag, or blocks per project policy)
- exit 3 → the manifest was edited after the hash was committed (PR is blocked)

## Workflow file

Drop this in `.github/workflows/prml.yml`:

```yaml
name: PRML verification

on:
  pull_request:
    paths:
      - "eval/manifest.yaml"
      - "eval/manifest.hash"
      - "eval/eval.log"
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: studio-11-co/prml-verify-action@v1
        with:
          manifest: eval/manifest.yaml
          hash-file: eval/manifest.hash
          mode: guard           # guard | verdict | lock
          falsify-version: 0.1.4
```

## Three modes

| Mode | What it does | When to use |
|---|---|---|
| `guard` | Verifies the manifest hashes to the recorded value. Blocks the PR if not. | Most projects. The 80% case. |
| `verdict` | Also checks the recorded `value` against the threshold (using `threshold_direction`). Exit 10 on threshold fail. | When your CI is also the publication gate. |
| `lock` | Refuses any PR that *modifies* an existing committed manifest, regardless of hash. | Strict mode for shipped releases. |

## What goes wrong

**1. Forgetting to commit `manifest.hash`.** The workflow runs, sees no hash file, and emits a warning. Add a pre-commit hook that runs `falsify lock` and writes the hash to `manifest.hash` in the same commit.

**2. Forgetting that `verdict` mode requires `eval.log`.** The action doesn't run your eval. It checks the recorded `value` field against the threshold. If `value` is empty, `verdict` mode passes by default (no claim to verify). If you want to require a value to be present, add a separate lint step.

**3. Branch protection bypass.** Without GitHub branch protection, anyone with push access to `main` can edit `manifest.yaml` directly without going through PR. Enable "Require status checks to pass" with the PRML workflow as a required check.

## What doesn't work

- **Verifying execution.** The Action verifies what was *committed*, not what was *run*. A determined publisher can pre-register, run on a different model, and lie in the `value` field. PRML §8.1 names this. Combine with a Sigstore-attested run for execution integrity.

- **Cross-repo verification.** The Action only sees the repo it runs in. If your manifest is in repo A and the model artifact is in repo B, you need a second step that pulls the artifact and re-derives.

- **Replacing branch protection.** This is a lint, not an authorisation system. Branch protection still does the actual gate-keeping.

## CI surface — minimum viable

The smallest possible CI gate is one shell line:

```bash
falsify verify eval/manifest.yaml --hash "$(cat eval/manifest.hash)"
```

Drop that in any CI provider that supports POSIX shell. The Action is convenience, not necessity.

## Next pattern

If you want to publish your hash for community verification: see [Pattern 6 — Public registry anchoring](06-registry-anchor.md).
