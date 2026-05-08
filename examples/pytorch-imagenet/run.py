#!/usr/bin/env python3
"""
ImageNet val eval with PRML pre-registration.

Lock manifest before the run; eval; emit observed value next to the locked hash.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# These are the production dependencies; left unimported here so the example
# file is readable without pulling in torch.
#   import torch
#   import torchvision
#   from torchvision.models import resnet50, ResNet50_Weights


HERE = Path(__file__).parent
MANIFEST = HERE / "manifest.yaml"
HASH_FILE = HERE / "manifest.hash"
RESULT_FILE = HERE / "eval-result.json"


def lock_manifest() -> str:
    """Use the falsify CLI to compute a deterministic hash."""
    result = subprocess.run(
        ["falsify", "lock", str(MANIFEST)],
        capture_output=True,
        text=True,
        check=True,
    )
    h = result.stdout.strip()
    HASH_FILE.write_text(h + "\n")
    return h


def verify(expected_hash: str) -> None:
    subprocess.run(
        ["falsify", "verify", str(MANIFEST), "--hash", expected_hash],
        check=True,
    )


def run_eval() -> float:
    """Stand-in for the real ImageNet eval. Replace with your loop.

    Returns top-1 accuracy as a float in [0, 1].
    """
    # ---- Replace with real eval --------------------------------------
    # weights = ResNet50_Weights.IMAGENET1K_V2
    # model = resnet50(weights=weights).eval().half().cuda()
    # transform = weights.transforms()
    # dataset = torchvision.datasets.ImageNet(root="data/imagenet", split="val",
    #                                          transform=transform)
    # loader = torch.utils.data.DataLoader(dataset, batch_size=64, num_workers=8)
    # correct = total = 0
    # with torch.inference_mode():
    #     for imgs, labels in loader:
    #         imgs, labels = imgs.cuda().half(), labels.cuda()
    #         out = model(imgs)
    #         correct += (out.argmax(dim=1) == labels).sum().item()
    #         total += labels.size(0)
    # return correct / total
    # ------------------------------------------------------------------
    # For the example, return a placeholder. Real run will overwrite.
    return 0.9237  # placeholder


def main() -> int:
    # Step 1: lock before the run
    print("locking manifest…", file=sys.stderr)
    manifest_hash = lock_manifest()
    print(f"locked: {manifest_hash}", file=sys.stderr)

    # Step 2: run
    print("running eval…", file=sys.stderr)
    accuracy = run_eval()

    # Step 3: emit observed value alongside the locked hash
    result = {
        "manifest_hash": manifest_hash,
        "metric": "accuracy",
        "observed_value": accuracy,
        "threshold": 0.92,
        "threshold_direction": ">=",
        "verdict": "pass" if accuracy >= 0.92 else "fail",
    }
    RESULT_FILE.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

    # Step 4: post-run sanity verify
    print("verifying manifest…", file=sys.stderr)
    verify(manifest_hash)
    print("ok", file=sys.stderr)

    return 0 if result["verdict"] == "pass" else 10


if __name__ == "__main__":
    raise SystemExit(main())
