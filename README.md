# tujia-tts

Text-to-speech for **Northern Tujia (Longshan Miaoertan standard pronunciation)**.
Input is **Ye pinyin** (`hufnix davhar niev caif kax`) or **toned IPA** (`xu21 ni21`),
output is **16 kHz mono** speech.

> **v0.5.0a1 preview — single speaker, `badou` only.**
> Weights: `vits_tujia-v0.5` (4.66 h / 9,757 clips, 17 source speakers voice-converted to
> the badou timbre, validation mel loss 0.4700 at epoch 162).
> Training is still running and the duration predictor shows sentence-level drift; treat
> this as a preview, not a stable release.
> The ONNX graph has no speaker input, so there is no second voice to select.
> Details and limitations: [MODEL_CARD.md](MODEL_CARD.md).

This repository carries the released model, the text front-end, and evaluation notes.
Data production and training are not part of this repository.

## Install

```bash
python3 -m pip install tujia-tts          # pulls onnxruntime, numpy, tujia-nlp
tujia-tts --text "hufnix davhar niev caif kax" -o out.wav
tujia-tts --text "xu21 ni21" -o out.wav --notation ipa
```

Or use it as a library:

```python
from tujia_tts import synthesize, write_wav

audio, sr, n_unknown, n_ids = synthesize("af gov diex caf")
write_wav("out.wav", audio, sr)
```

Both **Ye pinyin** and **toned IPA** are accepted; the notation is detected automatically
(`--notation ye|ipa` forces it). `n_unknown > 0` means some syllables or symbols did not
enter the phoneme table — check the spelling, or note that Chinese characters are not
supported (they raise if nothing usable is left).

## Versions

| Version | Data | Engine | Status |
|---|---|---|---|
| v0.1 | 2,390 clips / 1.87 h, male teacher | VITS | Failed the intelligibility probe; not released |
| v0.2 | 3,403 clips / 4.10 h, unified to `badou` | VITS + ONNX | Superseded by v0.3 |
| v0.3 | 3,958 clips / 6.40 h, unified to `badou` | VITS + ONNX | Superseded by v0.4 |
| v0.4 | 3,881 clips / 6.47 h, unified to `badou` | VITS + ONNX | Superseded by v0.5 |
| v0.5.0a1 | 9,757 clips / 4.66 h, 17 speakers VC'd to `badou` | VITS + ONNX | **Preview release** |

A version ships only after the intelligibility probe, never on training loss alone.

## Pre- and post-processing

Text: corpus notation normalisation (`*loanword*2`, `bi2zi1ka3`, `A:` tags, syllable-final
`y`→`v`) → syllable split and initial/final parsing by **[tujia-nlp](https://github.com/ibaibing/TujiaNLP)**
(`tujia_nlp.corpus`) → IPA (`z/c/s/r + i → ɿ`) → one tone token per syllable
(unmarked syllables read as 21 = `T3`) → unknown symbols dropped and counted. IPA input
skips the first two steps.

Waveform: trim leading/trailing silence (−40 dBFS, 30 ms margin) → peak normalise to
−1 dBFS → 10 ms fade. `--no-trim` keeps raw length; `--target-dbfs` changes the target.

**Output is deterministic.** The stochastic duration predictor is seeded at export, so the
same text in the same environment produces the same length in every process. v0.2 could
swing between 1.2 s and 2.8 s for one sentence; use `length_scale` for deliberate speed
changes.

## Evaluation

| Metric | v0.4 | v0.5.0a1 (preview) |
|---|---|---|
| ASR error rate, 100 held-out sentences (synthesized) | **0.972** | not run yet |
| ASR error rate, same sentences (human recordings) | 0.804 | not run yet |
| Validation mel loss | 0.4195 | 0.4700 (not comparable, different split) |
| Median syllable duration (human: 222 ms) | 221 ms | under review |
| Energy in the last 100 ms, relative to the whole clip | **0.000** | under review |

v0.5 is trained from scratch on a different corpus split and a 40-symbol inventory, so its
validation loss is not on the same scale as v0.4. The round-trip ASR probe and duration
statistics will be filled in once training finishes; do not treat the preview as a quality
improvement over v0.4 yet.

Tone acceptance by native listeners is collected per release and recorded in `releases/`.

## Layout

```
README.md                  this file
MODEL_CARD.md              model card (training, metrics, limitations)
LICENSE                    MIT (code)
NOTICE                     usage boundaries for weights
requirements.txt           inference dependencies
pyproject.toml             tujia-tts package metadata
src/tujia_tts/             front-end (Ye pinyin / IPA), synthesis, post-processing
src/tujia_tts/data/        vits_tujia-v0.5.onnx + piper-style config
examples/                  sample outputs with their input text
docs/usage.md              install, devices, sample-rate notes
docs/note.md               long-form technical and usage note
releases/                  per-version release notes
release/upload.sh          GitHub / Hugging Face / ModelScope / PyPI helper
```

## Related

| Repository | Role |
| --- | --- |
| [TujiaNLP](https://github.com/ibaibing/TujiaNLP) | Corpus, orthography utilities (this package depends on `tujia-nlp`) |
| [tujia-asr](https://github.com/ibaibing/tujia-asr) | The reverse direction: speech → syllables |
| [tujia-llm](https://github.com/ibaibing/tujia-llm) | Language model layer |

## License

- Code: MIT
- Model weights: research use only; no rights to recordings, transcripts, or speaker voices
