# Pattern 13 — runnable composition

`pattern13_prml_commit_reveal.py` makes the co-authored Pattern 13 executable end to end:
PRML pre-registration + a valichord_attestation-style bundle + a local commit-reveal round,
then three adversarial cases showing each layer catches what the others can't.

```
python3 pattern13_prml_commit_reveal.py
```

Honesty: the PRML layer uses the real `falsify_prml` reference; the bundle hashing
(Merkle root, bundle_hash/content_hash) is real crypto matching the v1.2 format; the
commit-reveal is real crypto but simulated locally (production ValiChord runs on
Holochain across isolated nodes). No network, stdlib only.
