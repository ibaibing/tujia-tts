# Release helper — mirrors the tujia-llm / tujia-asr layout.
#   huggingface-cli login          (or: hf auth login)
#   modelscope login --token <token>
#   twine upload dist/*            (PyPI token via ~/.pypirc or TWINE_PASSWORD)
#
#   bash release/upload.sh         stage + checksum, then push to HF / ModelScope
#   PYPI=1 bash release/upload.sh  print the PyPI command only
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${VERSION:-v0.2}"
ORG="${ORG:-TujiaNLP}"
REPO="${REPO:-tujia-tts-${VERSION}}"
MODEL="${MODEL:-$ROOT/src/tujia_tts/data/vits_tujia-v0.2.onnx}"
CFG="${CFG:-$ROOT/src/tujia_tts/data/vits_tujia-v0.2.onnx.json}"

STAGE="$(mktemp -d)"

cp "$MODEL" "$STAGE/"
cp "$CFG" "$STAGE/"
cp "$ROOT/MODEL_CARD.md" "$STAGE/README.md"
cp "$ROOT/NOTICE" "$STAGE/NOTICE"
cp "$ROOT/LICENSE" "$STAGE/LICENSE"
cp "$ROOT/docs/usage.md" "$STAGE/usage.md"

( cd "$STAGE" && shasum -a 256 ./*.onnx ./*.json > SHA256SUMS )

tar -czf "$STAGE/${REPO}.tar.gz" -C "$STAGE" \
  "$(basename "$MODEL")" "$(basename "$CFG")" README.md NOTICE LICENSE usage.md

echo "==> staging: $STAGE"
ls -lh "$STAGE"

echo "==> Hugging Face"
huggingface-cli repo create "$ORG/$REPO" --type model -y 2>/dev/null || true
huggingface-cli upload "$ORG/$REPO" "$STAGE" . --commit-message "release ${VERSION}"

echo "==> ModelScope"
modelscope upload "$ORG/$REPO" "$STAGE" --commit-message "release ${VERSION}" 2>/dev/null || \
  echo "Create the ModelScope repository first: https://modelscope.cn/models/$ORG/$REPO"

echo "==> GitHub Release"
echo "Attach $STAGE/${REPO}.tar.gz and $STAGE/SHA256SUMS to:"
echo "https://github.com/ibaibing/tujia-tts/releases/new?tag=$VERSION"

echo "==> PyPI"
python3 -m build --wheel
echo "twine upload dist/tujia_tts-*.whl"
