---
license: other
license_name: research-preview
license_link: https://github.com/ibaibing/tujia-tts/blob/main/NOTICE
library_name: onnxruntime
pipeline_tag: text-to-speech
language:
  - zh
tags:
  - tujia
  - low-resource
  - tts
  - vits
  - onnx
  - single-speaker
---

# Model Card — tujia-tts v0.2

## Overview

`vits_tujia-v0.2` is a single-speaker Tujia text-to-speech model. Input is **Ye pinyin**
(the Ye De-shu transcription, tone letters `x / f / r / v`), output is **16 kHz mono**
speech in **one voice only: badou**.

There is no speaker conditioning: the model's `SynthesizerTrn` is single-speaker, so the
ONNX graph has exactly three inputs (`input`, `input_lengths`, `scales`) and **no `emb_g`
/ `sid` channel**. Switching the voice requires switching the model file.

This is a low-resource research release: the model is intelligible on common vocabulary
but has the failure modes listed below.

## Training

| Item | Value |
|---|---|
| Source run | `tujia-tts-lab` Run B, epoch 113 |
| Checkpoint | `epoch=0113`, validation mel loss 0.5108 |
| Data | 3,403 clips / 4.10 h, four sources, timbre unified to **badou** (Seed-VC) |
| Speakers | 1 (`num_speakers=1`, empty `speaker_id_map`) |
| Sample rate | 16,000 Hz |
| Symbols | 41 (IPA phones + `T0`–`T4` tone tokens) |
| Export | ONNX opset 15 + piper-style `.onnx.json` |

Training corpora are internal-only and are **not** distributed here.

## Input format

Ye pinyin using the four tone letters of Ye De-shu (1984): `x`=55, `f`=35, `r`=21, `v`=53.

```
hufnix davhar niev caif kax
af gov diex caf
```

The front-end (`tujia_tts.ye_phonemes`) normalises corpus notation (`*loanword*2`, `bi2zi1ka3`,
`A:` speaker tags, syllable-final `y`→`v`), splits syllables, maps initials/finals to IPA
(with `z/c/s/r + i → ɿ`), and appends one tone token per syllable. Chinese characters are
not supported.

## Pre- and post-processing

Text side: notation normalisation → syllable split (DP, longest-first) → IPA → tone token →
unknown symbols dropped and counted (never a silent `KeyError`) → empty input raises.

Waveform side (`postprocess()`): trim leading/trailing silence (−40 dBFS relative to peak,
30 ms margin) → peak normalise to −1 dBFS → 10 ms fade in/out.

## Evaluation

| Metric | Value |
|---|---|
| Phone error rate, 40 sentence probes (synthesized) | 0.784 (median) |
| Phone error rate, same probes (human audio) | 0.567 |
| Speaker cosine to studio badou reference | 0.814 (training target itself: 0.812) |

## Known limitations

1. **Duration is stochastic across processes.** The exported graph contains
   `/dp/RandomNormalLike` (VITS stochastic duration predictor) whose `scale` was frozen at
   export time and is not driven by `noise_scale`. The same text can vary between 1.2 s and
   2.8 s from one process to the next. Pin the node's seed (see
   `scripts` in `tujia-tts-lab`) if byte-identical output is required.
2. **Tone is approximate.** Tone tokens are trained from corpus annotation; sandhi and
   emphatic lengthening are not modelled.
3. **Short single-syllable words are the weakest.** They are most sensitive to the
   duration noise above.
4. **No prosody control.** No SSML, breaks, or emphasis.
5. **One speaker only.** No voice conversion, no cloning, no multi-speaker selection.
6. **Not a piper voice.** `phoneme_type: "text"` with two-character tone tokens; the
   standard `piper` front-end (espeak-ng) cannot drive this model. Use the bundled
   front-end.

## Intended use

Suitable: research on low-resource TTS, community demo material reviewed by native
speakers, and prototyping Tujia audio interfaces.

Not suitable: publication or teaching material without native-speaker review, any claim
that the output is a real person's recording, or commercial redistribution.

## Licensing and ethics

Code is MIT. Weights are research-use only under `NOTICE`. Speaker consent has not been
confirmed per source recording; commercial use or redistribution requires a rights review.
Tujia is endangered — outputs should be reviewed by native speakers before community or
educational use.

## Version history

| Version | Data | Notes |
|---|---|---|
| v0.1 | 1.87 h / 2,390 clips, male teacher | Failed intelligibility probe; not released |
| v0.2 | 4.10 h / 3,403 clips, unified to badou | First public release |
