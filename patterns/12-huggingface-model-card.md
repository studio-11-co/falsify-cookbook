# Pattern 12 — PRML in Hugging Face model cards

> **When to use:** You publish a model to the Hugging Face Hub and the model card states an accuracy number. You want that number to be *verifiable* — re-derivable by anyone who pulls the repo — instead of trust-me prose that can be edited after the fact.

## The shape

A Hugging Face model card is the default place teams report eval numbers, and (for high-risk systems) the artifact a reviewer reaches for under EU AI Act Annex IV. But a model card is post-hoc editable prose: nothing in it proves *when* the threshold was set relative to seeing the result. PRML is the evidence layer underneath the card.

The convention is three files and one paragraph:

1. The PRML manifest, locked before the run, committed into the model repo under `.prml/`.
2. Its `spec.lock.json` sidecar next to it.
3. A short block in the card body: the claim in plain English, the SHA-256, and a one-line "how to verify".

Anyone who clones the repo re-derives the hash and checks it against the card — with `falsify-js` (the PRML reference CLI), a Go/Rust reference binary, or by pasting the manifest at [registry.falsify.dev](https://registry.falsify.dev). The card's number stops being an assertion and becomes a receipt.

## Author and lock locally (before the run)

Write the manifest as a file, e.g. `imagenet-acc.prml.yaml`:

```yaml
version: prml/0.1
claim_id: 01900000-0000-7000-8000-000000000031
created_at: "2026-05-29T09:00:00Z"
metric: accuracy
comparator: ">="
threshold: 0.90
dataset:
  id: imagenet-1k
  hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855   # sha256 of the pinned dataset revision (64 lowercase hex; see Pattern 4)
  uri: https://huggingface.co/datasets/ILSVRC/imagenet-1k
seed: 42
producer:
  id: falsify.dev                        # your org/domain
model:
  id: your-org/your-model
```

Lock it with the PRML reference CLI (canonicalizes, hashes, writes a sidecar):

```bash
npm install -g falsify-js js-yaml          # the reference CLI; js-yaml lets it read .yaml
falsify-js lock imagenet-acc.prml.yaml
# locked  sha256: <64-hex digest>          (sidecar: imagenet-acc.prml.prml.sha256)
```

(Go and Rust reference binaries, and the in-browser tool at registry.falsify.dev, produce the byte-identical hash.)

Then run the eval and record the verdict. The hash is now frozen; editing the spec afterwards breaks it.

## Push it into the model repo

```python
from huggingface_hub import HfApi

api = HfApi()
repo = "your-org/your-model"

# ship the manifest so the claim is re-derivable from the repo itself
api.upload_file(
    path_or_fileobj="imagenet-acc.prml.yaml",
    path_in_repo=".prml/imagenet-acc.prml.yaml",
    repo_id=repo,
    repo_type="model",
    commit_message="Add pre-registered PRML eval manifest",
)
```

## The card block

Add to the model card body (the README's prose, below the metric):

```markdown
## Evaluation claim (pre-registered)

**accuracy >= 0.90 on imagenet-1k (rev <commit-sha>), seed 42.**
Committed before the run as a PRML manifest:
`sha256:85c120acc427dbd9755429b019d6cb2b20b5a8faa61f32fa1700ed24990d7249`

Verify (no install): paste `.prml/imagenet-acc.prml.yaml` at https://registry.falsify.dev and re-derive the hash. Or with the reference CLI:

    npm install -g falsify-js js-yaml
    falsify-js verify .prml/imagenet-acc.prml.yaml --observed 0.934
    # PASS  metric=accuracy  observed=0.934  >=  threshold=0.9   (exit 0)
    # exit 3 = TAMPERED (hash mismatch) · exit 10 = FAIL (below threshold)

Public anchor: https://registry.falsify.dev/<hash>
```

Optionally also fill the standard Hugging Face `model-index` `eval_results` in the card front matter so the number renders in the Hub UI — but treat `model-index` as the *display* and the PRML hash as the *proof*. The front matter is editable; the hash is not.

## What goes wrong

**1. Hash in the card, no manifest in the repo.** Pasting `sha256:...` into the card without uploading `.prml/.../spec.yaml` gives readers nothing to recompute against. The hash is only meaningful next to the bytes it commits. Upload the manifest first, quote the hash second.

**2. `dataset.hash` left as a placeholder.** `hf:revision-<commit-sha>` must be a real pinned revision. If you point at the dataset's default branch, the benchmark can change under you and a re-derivation months later won't reproduce — and you won't be able to tell drift from tampering. Pin the revision SHA from the dataset's commit history.

**3. Locking after you saw the number.** The whole guarantee is pre-commitment. If you `falsify lock` after the run "to tidy up", you have a hash but not evidence — and a reviewer who asks "when was the threshold set?" gets the same trust-me answer a bare model card gives. Lock before. See [Anti-pattern A1](../anti/A1-late-hash.md).

**4. Gated or private model repo.** The manifest hash is public-safe (it must contain no private data — see [Anti-pattern A3](../anti/A3-private-data.md)), but if the manifest *file* sits behind a gate, outsiders can't re-derive it. For claims you want third parties to verify (auditors, customers), also anchor the hash to the public registry (Pattern 6) so verification doesn't depend on repo access.

**5. Editing the card to "fix a typo" in the claim.** Changing the threshold or metric text in the card so it no longer matches the committed manifest produces a card that contradicts its own hash. Don't edit a published claim; revoke and re-issue. See [Anti-pattern A2](../anti/A2-typo-edit.md) and [Pattern 7 — Revocation](07-revocation.md).

## What doesn't work

- **Proving the eval was actually run on that model.** PRML verifies what was *committed*, not what was *executed*. A publisher can pre-register, run on a different checkpoint, and record a flattering number. PRML §8.1 names this. For execution integrity, attest the run with Sigstore — see [Pattern 11](11-sigstore-execution.md).

- **Native Hub rendering.** The Hub will not render or validate PRML for you; this is a convention you adopt, not a Hub feature. The value is that *anyone* can verify with the reference CLI or the in-browser registry, with or without Hub support.

- **Replacing the model card.** This sits *under* the card, it doesn't replace it. The card stays the human-readable summary; PRML makes one specific claim on it checkable. (Background: [Model cards vs pre-registration](https://falsify.dev/notes/model-cards-vs-pre-registration/).)

## Next pattern

For execution integrity on top of this, see [Pattern 11 — PRML + Sigstore](11-sigstore-execution.md). To publish the hash for verification that doesn't depend on repo access, see [Pattern 6 — Public registry anchoring](06-registry-anchor.md).
