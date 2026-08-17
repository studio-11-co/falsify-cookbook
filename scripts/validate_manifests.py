#!/usr/bin/env python3
"""Validate every PRML manifest printed in this cookbook against the real reference.

Why this exists: the cookbook shipped manifests that a conforming implementation
must reject (a non-UUIDv7 `claim_id`, a `notes: |` block scalar carrying newlines).
Nobody noticed, because nothing executed the examples or read the YAML in the docs.
Reported from outside — falsify-cookbook#4 — 40 days after it was opened.

Checks:
  1. every manifest in the docs validates — ```yaml fences and shell heredocs alike
     (blank copy/paste skeletons are skipped on purpose)
  2. every 64-hex digest printed outside a manifest block equals that manifest's hash
  3. every heredoc manifest is already in canonical form, so the `sha256sum` the doc
     tells the reader to run returns the same hash a conforming verifier derives
  4. every runnable example under patterns/examples/ exits 0

Run: python3 scripts/validate_manifests.py
"""

import glob
import hashlib
import os
import re
import subprocess
import sys
import tempfile

try:
    import falsify_prml as prml
except ImportError:
    sys.exit("Needs the PRML reference. Run: pip install falsify")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLANK = re.compile(r':\s*""')          # copy/paste skeleton, not a manifest
failures = []


YAML_BLOCK = re.compile(r"```ya?ml\n(.*?)```", re.S)
# Pattern 8 writes its manifest through a shell heredoc inside a ```bash fence,
# so a yaml-fence-only scan would silently skip it.
HEREDOC = re.compile(r"<<'?EOF'?\n(.*?)\nEOF", re.S)


def blocks(src):
    for m in YAML_BLOCK.finditer(src):
        yield m
    for m in HEREDOC.finditer(src):
        yield m


def check_docs():
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        src = open(path).read()
        rel = os.path.relpath(path, ROOT)
        for m in blocks(src):
            block = m.group(1)
            if "claim_id" not in block or BLANK.search(block):
                continue
            line = src[:m.start()].count("\n") + 2
            tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
            tmp.write(block)
            tmp.close()
            manifest = None
            try:
                manifest = prml.load_manifest(tmp.name)
                errs = prml.validate_manifest(manifest)
            except Exception as exc:                      # parse failure counts
                errs = [f"parse error: {exc}"]
            finally:
                os.unlink(tmp.name)
            if errs:
                failures.append(f"{rel}:{line} — {'; '.join(errs)}")
                continue
            print(f"  ok  {rel}:{line}")
            check_published_hash(rel, src, manifest, block,
                                 m.re is HEREDOC)


def check_published_hash(rel, src, manifest, block, is_heredoc):
    """Two checks the docs failed silently before this script existed.

    1. Any 64-hex digest a doc prints OUTSIDE its manifest blocks is presented to the
       reader as that manifest's hash. Pattern 12 published one that did not match the
       manifest printed directly above it, so following the verify steps gave a mismatch.
    2. A manifest written to disk by a shell heredoc is hashed by `sha256sum` as raw
       file bytes, so those bytes must already BE the canonical bytes. Pattern 8 was
       written in unsorted, fully-quoted YAML, so its `sha256sum` output could never
       equal the hash any conforming verifier derives.
    """
    actual = prml.manifest_hash(manifest)
    inside = "\n".join(m.group(1) for m in blocks(src))
    for m in re.finditer(r"\b[0-9a-f]{64}\b", src):
        if m.group(0) in inside or m.group(0) == actual:
            continue
        line = src[:m.start()].count("\n") + 1
        failures.append(f"{rel}:{line} — published digest {m.group(0)[:12]}… "
                        f"is not this manifest's hash ({actual[:12]}…)")

    if is_heredoc:
        on_disk = hashlib.sha256((block + "\n").encode()).hexdigest()
        if on_disk != actual:
            failures.append(
                f"{rel} — heredoc manifest is not in canonical form: sha256sum of the "
                f"file it writes is {on_disk[:12]}…, PRML hash is {actual[:12]}…")


def check_examples():
    for path in sorted(glob.glob(os.path.join(ROOT, "patterns", "examples", "*.py"))):
        rel = os.path.relpath(path, ROOT)
        run = subprocess.run([sys.executable, path], capture_output=True, text=True)
        if run.returncode != 0:
            tail = (run.stderr or run.stdout).strip().splitlines()[-3:]
            failures.append(f"{rel} — exit {run.returncode}: {' / '.join(tail)}")
        else:
            print(f"  ok  {rel}")


print("manifests in the docs:")
check_docs()
print("runnable examples:")
check_examples()

if failures:
    print("\nFAIL")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("\nall manifests valid, all examples run")
