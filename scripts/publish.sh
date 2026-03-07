#!/usr/bin/env bash
# scripts/publish.sh — build and publish the package to PyPI (or TestPyPI).
set -euo pipefail

TESTPYPI=false

for arg in "$@"; do
  case $arg in
    --test) TESTPYPI=true ;;
  esac
done

echo "==> Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info

echo "==> Installing/upgrading build tools..."
python -m pip install --upgrade pip build twine

echo "==> Building source distribution and wheel..."
python -m build

echo "==> Checking distribution artifacts..."
python -m twine check dist/*

if [ "$TESTPYPI" = "true" ]; then
  echo "==> Uploading to TestPyPI..."
  python -m twine upload --repository testpypi dist/*
  echo ""
  echo "Install from TestPyPI with:"
  echo "  pip install --index-url https://test.pypi.org/simple/ llm-output-guard"
else
  echo "==> Uploading to PyPI..."
  python -m twine upload dist/*
  echo ""
  echo "Install with: pip install llm-output-guard"
fi
