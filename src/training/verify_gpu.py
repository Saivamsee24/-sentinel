"""Verify that XGBoost can use your GPU before you waste 15 minutes finding out it can't.

XGBoost silently falls back to CPU if anything is wrong with the CUDA setup. This
script forces a tiny GPU training run and reports clearly whether it worked.

Usage:
    python -m src.training.verify_gpu
"""

from __future__ import annotations

import sys
import time

from sklearn.datasets import make_classification
from xgboost import XGBClassifier


def check_xgboost_version() -> bool:
    """XGBoost >= 2.0 has the unified `device='cuda'` API."""
    import xgboost

    version = xgboost.__version__
    major = int(version.split(".")[0])
    print(f"XGBoost version: {version}")
    if major < 2:
        print("  ✗ Need XGBoost >= 2.0. Run: pip install -U xgboost")
        return False
    print("  ✓ Version OK")
    return True


def check_cuda_available() -> bool:
    """Try a tiny GPU fit. Returns True if it succeeds, False otherwise."""
    try:
        X, y = make_classification(n_samples=1000, n_features=20, random_state=0)
        model = XGBClassifier(
            n_estimators=10,
            tree_method="hist",
            device="cuda",
            verbosity=0,
        )
        t0 = time.time()
        model.fit(X, y)
        elapsed = time.time() - t0
        print(f"  ✓ GPU training succeeded ({elapsed:.2f}s for 10 trees on 1k rows)")
        return True
    except Exception as e:
        print(f"  ✗ GPU training failed: {e}")
        return False


def benchmark_speedup() -> None:
    """Train the same small model on CPU and GPU; report the speedup ratio."""
    print("\nRunning CPU-vs-GPU benchmark (synthetic 50k × 50)...")
    X, y = make_classification(n_samples=50_000, n_features=50, random_state=0)
    base = dict(n_estimators=200, max_depth=6, tree_method="hist", verbosity=0)

    t0 = time.time()
    XGBClassifier(**base, device="cpu").fit(X, y)
    cpu_time = time.time() - t0
    print(f"  CPU: {cpu_time:.2f}s")

    t0 = time.time()
    XGBClassifier(**base, device="cuda").fit(X, y)
    gpu_time = time.time() - t0
    print(f"  GPU: {gpu_time:.2f}s")

    if gpu_time < cpu_time:
        print(f"  ✓ Speedup: {cpu_time / gpu_time:.1f}×")
    else:
        print("  ⚠ GPU was not faster — possible silent fallback. Check `nvidia-smi`.")


def main() -> int:
    print("=" * 60)
    print("XGBoost GPU verification")
    print("=" * 60)

    print("\n[1/2] Checking XGBoost version...")
    if not check_xgboost_version():
        return 1

    print("\n[2/2] Smoke-testing GPU training...")
    if not check_cuda_available():
        print("\nGPU is not usable. Common fixes on Windows:")
        print("  - Update NVIDIA drivers (need >= 525): https://www.nvidia.com/Download/")
        print("  - Run `nvidia-smi` in PowerShell — should list your GPU")
        print("  - Reinstall xgboost: pip install --upgrade --force-reinstall xgboost")
        return 1

    benchmark_speedup()
    print("\n" + "=" * 60)
    print("✓ GPU is ready. Run: python -m src.training.train")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())