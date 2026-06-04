# Pattern 5 — CI gate via `prml-verify-action`

> **When to use:** Your repo commits PRML manifests under `.falsify/`, and you want PRs that ship a tampered or regressed eval claim to be automatically blocked at merge time.

## The shape

PRML manifests live in your repo under `.falsify/<claim-name>/spec.yaml`, locked once with `falsify lock` so a `spec.lock.json` sits next to each one. A GitHub Action runs on every PR and:

- exit 0 → all locked claims hash to their recorded values and pass their thresholds (PR proceeds)
- exit 10 → at least one claim regressed below its threshold (PR blocks — this is a FAIL)
- exit 3 → at least one locked manifest was edited after locking, or a pinned `expected-hash` doesn't match (PR blocks — this is a TAMPER)
- exit 2 → bad inputs (e.g. `mode: verdict` without a `claim` value)

## Workflow file

Drop this in `.github/workflows/prml.yml`:

```yaml
name: PRML verification

on:
  pull_request:
    paths:
      - ".falsify/**"
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - uses: studio-11-co/prml-verify-action@v2
        with:
          mode: guard
          falsify-version: "0.1.4"
```

`@v2` is a moving tag that tracks the latest 2.x release (currently `v2.0.3`). Pin to `@v2.0.3` instead if you want zero supply-chain surprises. Both `checkout` and `setup-python` are on `@v6` to match the action's own internal pinning standard — older majors still work but won't get future security backports on the runner-images timeline.

## Three modes

The `mode` input drives everything:

| Mode | What it does | When to use |
|---|---|---|
| `guard` (default) | Scans every directory under `.falsify/`, verifies each lock, fails the build on any FAIL (exit 10) or TAMPER (exit 3). | Most projects. The 80% case. One step, no inputs. |
| `verdict` | Verifies a single named claim. Requires the `claim` input. Optionally pins to `expected-hash`. Exit 10 on threshold fail, exit 3 on tamper or hash mismatch. | When CI is also the publication gate and you want to surface one specific receipt. |
| `lock` | Computes and writes a new `spec.lock.json`. Requires the `claim` input. | Rare in CI — locking should happen once, locally, *before* the experiment runs. If you need it in CI, it's almost always a sign the manifest isn't pre-registered. |

## Inputs you actually care about

| Input | Default | Notes |
|---|---|---|
| `mode` | `guard` | `guard` / `verdict` / `lock` |
| `claim` | `""` | Required when `mode` is `verdict` or `lock` |
| `expected-hash` | `""` | If set in `verdict` mode, computed hash must match or the action exits 3 |
| `falsify-version` | `0.1.4` | PyPI pin for the reference CLI. Bump deliberately. |
| `python-version` | `3.11` | The Python the action installs `falsify` against |
| `working-directory` | `.` | Set if `.falsify/` lives in a subdirectory |
| `anchor-to-registry` | `false` | Only set `true` when you want a public receipt — see Pattern 6 |

Outputs: `status` (`pass`/`fail`/`tamper`/`inconclusive`), `hash` (the SHA-256 of the canonical manifest bytes, in `verdict` mode), `permalink` and `badge-snippet` (only when anchored).

## Pinning a known-good hash

If you've anchored a claim publicly and want CI to fail on *any* drift — not just internal lock mismatch — pin the hash:

```yaml
- uses: actions/checkout@v6
- uses: studio-11-co/prml-verify-action@v2
  with:
    mode: verdict
    claim: imagenet-resnet50-baseline
    expected-hash: fb7403c40afe63d892bf4aea2c123fdd7fe85366b74a277875465c4cb3cbf19c
```

Now the action exits 3 if either the lock changed or the recorded hash drifts from the pinned value. This is the strongest CI gate PRML offers without bringing in a separate attestation system.

## What goes wrong

**1. `.falsify/` doesn't exist.** `mode: guard` will run `falsify guard` against an empty tree and the CLI returns a non-zero status. The action surfaces `status: inconclusive`. Fix: lock at least one claim locally with `falsify init <name> && falsify lock <name>` and commit the resulting `.falsify/<name>/` directory before merging this workflow.

**2. `mode: verdict` without a `claim` input.** The action fails fast with exit 2 and `::error::mode=verdict requires the 'claim' input.` in the log. Same for `mode: lock`. Always pair these modes with a `claim:` line.

**3. `expected-hash` mismatch.** The most useful failure mode and also the most confusing one. Exit 3, `status: tamper`, and a log line with both the expected and computed hashes. Usually means someone re-locked the claim (changing the bytes), edited `spec.yaml` after locking, or you pasted the wrong hash into the workflow. Re-derive locally with `falsify lock <claim>` and compare.

**4. Branch protection bypass.** Without GitHub branch protection, anyone with push access to `main` can edit a locked manifest directly and skip the PR check entirely. Enable "Require status checks to pass before merging" with the PRML workflow as a required check. The action is a lint, not an authorisation system.

**5. `falsify-version` drift.** If you bump `falsify-version` mid-project, the canonicalization rules could shift between minor versions and re-derive a different hash for byte-identical YAML. Pin the version in your workflow and the same version in your local `falsify lock` step. The defaults match (`0.1.4` on both sides today), but don't rely on that across upgrades.

## What doesn't work

- **Verifying execution.** The action verifies what was *committed*, not what was *run*. A determined publisher can pre-register, run on a different model, and lie in the recorded value. PRML §8.1 names this explicitly. Combine with a Sigstore-attested run for execution integrity.

- **Cross-repo verification.** The action only sees the repo it runs in. If the manifest lives in repo A and the model artifact lives in repo B, you need a second step that pulls the artifact and re-derives.

- **Replacing branch protection.** This is a lint. Branch protection still does the actual gatekeeping.

## Next pattern

If you want to publish your hash for community verification: see [Pattern 6 — Public registry anchoring](06-registry-anchor.md).
