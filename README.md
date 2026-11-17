# tujia-tts

Text-to-speech for **Northern Tujia (Longshan Miaoertan standard pronunciation)**.
Input is **Ye pinyin** (`hufnix davhar niev caif kax`), output is **16 kHz mono** speech.

> **v0.2 released — single speaker, `badou` only.**
> Weights: `vits_tujia-v0.2` (4.10 h / 3,403 clips, Run B epoch 113, val mel 0.5108).
> The ONNX graph has no speaker input, so there is no second voice to select.
> Details and limitations: [MODEL_CARD.md](MODEL_CARD.md).

Data production, training and experiments live in the private `tujia-tts-lab` repository;
this repository only carries the released model, the text front-end, and evaluation notes.

## Install

```bash
python3 -m pip install tujia-tts          # pulls onnxruntime + numpy, ships the ONNX model
tujia-tts --text "hufnix davhar niev caif kax" -o out.wav
```

Or use it as a library:

```python
from tujia_tts import synthesize, write_wav

audio, sr, n_unknown, n_ids = synthesize("af gov diex caf")
write_wav("out.wav", audio, sr)
```

`n_unknown > 0` means some syllables or symbols did not enter the phoneme table — check the
spelling, or note that Chinese characters are not supported (they raise if nothing usable
is left).

## Versions

| Version | Data | Engine | Status |
|---|---|---|---|
| v0.1 | 2,390 clips / 1.87 h, male teacher | VITS | Failed the intelligibility probe; not released |
| v0.2 | 3,403 clips / 4.10 h, unified to `badou` | VITS + ONNX | **Current release** |

A version ships only after the intelligibility probe, never on training loss alone.

## Pre- and post-processing

Text: corpus notation normalisation (`*loanword*2`, `bi2zi1ka3`, `A:` tags, syllable-final
`y`→`v`) → syllable split → IPA (`z/c/s/r + i → ɿ`) → one `T0`–`T4` tone token per syllable →
unknown symbols dropped and counted.

Waveform: trim leading/trailing silence (−40 dBFS, 30 ms margin) → peak normalise to
−1 dBFS → 10 ms fade. `--no-trim` keeps raw length; `--target-dbfs` changes the target.

**Duration is stochastic across processes.** The exported graph's stochastic duration
predictor (`/dp/RandomNormalLike`) was frozen at export and is not driven by `noise_scale`,
so the same text can differ from one process to the next. For reproducible output, patch
the node seed or draw from a fixed `length_scale`.

## Evaluation

| Metric | Value |
|---|---|
| Phone error rate, 40 sentence probes (synthesized) | 0.784 (median) |
| Phone error rate, same probes (human audio) | 0.567 |
| Speaker cosine to studio `badou` reference | 0.814 (training target: 0.812) |

Tone acceptance by native listeners is collected per release and recorded in `releases/`.

## Layout

```
README.md                  this file
MODEL_CARD.md              model card (training, metrics, limitations)
LICENSE                    MIT (code)
NOTICE                     usage boundaries for weights
requirements.txt           inference dependencies
pyproject.toml             tujia-tts package metadata
src/tujia_tts/             front-end (Ye pinyin), synthesis, post-processing
src/tujia_tts/data/        vits_tujia-v0.2.onnx + piper-style config
examples/                  sample outputs
docs/usage.md              install, devices, sample-rate notes
releases/                  per-version release notes
release/upload.sh          GitHub / Hugging Face / ModelScope / PyPI helper
```

## Related

| Repository | Role |
| --- | --- |
| [TujiaNLP](https://github.com/ibaibing/TujiaNLP) | Corpus, collection standards, licensing |
| `tujia-tts-lab` (private) | Training and experiments |
| [tujia-asr](https://github.com/ibaibing/tujia-asr) | The reverse direction: speech → syllables |
| [tujia-llm](https://github.com/ibaibing/tujia-llm) | Language model layer |

## License

- Code: MIT
- Model weights: research use only; no rights to recordings, transcripts, or speaker voices
