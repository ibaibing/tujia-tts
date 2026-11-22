# Usage notes — tujia-tts v0.4

## Install

```bash
python3 -m pip install tujia-tts
```

The wheel contains the ONNX model (about 63 MB), so no separate download is needed.
Python 3.9+; `onnxruntime` runs on CPU everywhere and uses the Apple/CoreML or CUDA
provider if you pass one explicitly.

## Command line

```bash
tujia-tts --text "hufnix davhar niev caif kax" -o out.wav
tujia-tts --text "xu21 ni21" -o out.wav --notation ipa
tujia-tts --text "af gov diex caf" -o a.wav --length-scale 1.1     # >1 slower
tujia-tts --text "af gov diex caf" -o a.wav --no-trim              # keep raw length
tujia-tts --text "af gov diex caf" -o a.wav --target-dbfs -3        # quieter peak
```

Both notations are accepted and auto-detected:

| Input | Meaning |
|---|---|
| `hufnix davhar` | Ye pinyin, tone letters `x/f/r/v` (= 55/35/21/53) |
| `xu21 ni21` / `xu²¹ ni²¹` / `xu˨˩ ni˨˩` | toned IPA, tone omitted → `T3` (21) |
| `bi2zi1ka3` | Ye pinyin with digit tones (also parsed) |

`--notation ye|ipa` forces one parser when auto-detection would mis-route a string.

`unknown` in the output must be `0`. A positive count means a syllable or symbol did not
map into the 41-symbol phoneme table: check the spelling. Chinese characters are
not supported and raise `ValueError` when nothing usable remains.

## Python API

```python
from tujia_tts import synthesize, write_wav, postprocess, tokenize

tokenize("af gov diex caf")        # (tokens, n_unknown)
tokenize("a35 ko53", notation="ipa")

audio, sr, n_bad, n_ids = synthesize(
    "hufnix davhar niev caif kax",
    length_scale=1.0,      # None → config value (1.0)
    noise_scale=0.667,     # acoustic noise
    noise_w=0.8,           # duration noise
    do_postprocess=True,   # trim + peak + fade
    notation="auto",       # "ye" / "ipa" / "auto"
)
audio = postprocess(audio, sr, do_trim=False)   # or post-process yourself
write_wav("out.wav", audio, sr)
```

`audio` is `float32` in [-1, 1] at 16 kHz.

## Reproducibility

The stochastic duration predictor is seeded when the graph is exported, so the same text
produces the same length across processes and runs. Use `length_scale` when you want
slower or faster speech, and `noise_scale` / `noise_w` if you need acoustic variation.
There is no random duration drift as in v0.2.

## Piper compatibility

The config looks piper-like (`piper_version`, `phoneme_type: "text"`) but is **not** a
piper voice: the phoneme table contains two-character tone tokens (`T0`–`T4`; unmarked syllables use `T3`) and the
"espeak voice" field is a placeholder. The standard `piper` front-end cannot drive this
model; use `tujia_tts` / `tujia-tts`.
