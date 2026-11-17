# Usage notes — tujia-tts v0.2

## Install

```bash
python3 -m pip install tujia-tts
```

The wheel contains the ONNX model (about 55 MB), so no separate download is needed.
Python 3.9+; `onnxruntime` runs on CPU everywhere and uses the Apple/CoreML or CUDA
provider if you pass one explicitly.

## Command line

```bash
tujia-tts --text "hufnix davhar niev caif kax" -o out.wav
tujia-tts --text "af gov diex caf" -o a.wav --length-scale 1.1     # >1 slower
tujia-tts --text "af gov diex caf" -o a.wav --no-trim              # keep raw length
tujia-tts --text "af gov diex caf" -o a.wav --target-dbfs -3        # quieter peak
```

`unknown` in the output must be `0`. A positive count means a syllable or symbol did not
map into the 41-symbol phoneme table: check the Ye pinyin spelling. Chinese characters are
not supported and raise `ValueError` when nothing usable remains.

## Python API

```python
from tujia_tts import synthesize, write_wav, postprocess

audio, sr, n_bad, n_ids = synthesize(
    "hufnix davhar niev caif kax",
    length_scale=1.0,      # None → config value (1.0)
    noise_scale=0.667,     # acoustic noise
    noise_w=0.8,           # duration noise
    do_postprocess=True,   # trim + peak + fade
)
audio = postprocess(audio, sr, do_trim=False)   # or post-process yourself
write_wav("out.wav", audio, sr)
```

`audio` is `float32` in [-1, 1] at 16 kHz.

## Reproducibility

The exported graph contains a stochastic duration predictor whose sampling node was frozen
at export time and ignores `noise_scale`, so **duration varies between processes**. If you
need byte-identical output, pin that node's seed in the ONNX file or rebuild the graph with
`noise_w=0`.

## Piper compatibility

The config looks piper-like (`piper_version`, `phoneme_type: "text"`) but is **not** a
piper voice: the phoneme table contains two-character tone tokens (`T0`–`T4`) and the
"espeak voice" field is a placeholder. The standard `piper` front-end cannot drive this
model; use `tujia_tts` / `tujia-tts`.
