# Example: PyTorch + ImageNet eval, PRML pre-registered

> Pattern 1 + 5 — single-shot eval claim, with a CI-verifiable hash.

## What this shows

Before running an ImageNet validation pass on a ResNet-50 checkpoint, we:

1. Compute the SHA-256 hash of the dataset
2. Author a PRML manifest committing to threshold `accuracy >= 0.92`
3. Lock the manifest hash and write it to `manifest.hash`
4. Run the eval
5. Verify the post-run log against the hash

If anyone later edits `manifest.yaml` (even a typo), step 5 fails with exit code 3.

## Files

- [`run.py`](run.py) — the eval driver (PyTorch)
- [`manifest.yaml`](manifest.yaml) — the PRML manifest
- [`manifest.hash`](manifest.hash) — the locked SHA-256 (committed to git)
- [`requirements.txt`](requirements.txt) — `torch`, `torchvision`, `falsify>=0.1.4`

## Run it

```bash
pip install -r requirements.txt

# 1. Compute dataset hash (one-time setup)
python3 -c "
import hashlib
h = hashlib.sha256()
with open('imagenet-val.tar', 'rb') as f:
    for chunk in iter(lambda: f.read(2**20), b''):
        h.update(chunk)
print(h.hexdigest())
"
# Paste result into manifest.yaml's dataset_hash field

# 2. Lock the manifest
falsify lock manifest.yaml > manifest.hash
cat manifest.hash
# sha256:...

# 3. Run the eval
python3 run.py

# 4. Verify
falsify verify manifest.yaml --hash "$(cat manifest.hash)"
# OK
```

## CI gate

Drop in `.github/workflows/prml.yml`:

```yaml
name: PRML
on: [pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: studio-11-co/prml-verify-action@v1
        with:
          manifest: manifest.yaml
          hash-file: manifest.hash
          mode: guard
```

## What this example deliberately doesn't do

- Train the model. The model checkpoint is assumed to exist; this is an *eval* example.
- Push the manifest to the public registry. That's optional — see Pattern 6.
- Verify the model weights. PRML commits the *claim*, not the artefact. Wrap with Sigstore for that.

## See also

- [Pattern 1 — Single-shot eval claim](../../patterns/01-single-shot-eval.md)
- [Pattern 4 — Dataset version pinning](../../patterns/04-dataset-pinning.md)
- [Pattern 5 — CI gate](../../patterns/05-ci-gate.md)
