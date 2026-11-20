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

# Model Card — tujia-tts v0.3

## Overview

`vits_tujia-v0.3` is a single-speaker Tujia text-to-speech model. Input is **Ye pinyin**
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
| Checkpoint | `vits_tujia-v0.3`, validation mel loss 0.4523 |
| Data | 3,958 clips / 6.40 h, timbre unified to **badou** |
| Speakers | 1 (`num_speakers=1`, empty `speaker_id_map`) |
| Sample rate | 16,000 Hz |
| Symbols | 41 (IPA phones + `T0`–`T4` tone tokens) |
| Export | ONNX opset 15 + piper-style `.onnx.json` |

Training corpora are internal-only and are **not** distributed here.

## Input format

Two notations are accepted; the package detects which one you used.

**Ye pinyin** with the four tone letters of Ye De-shu (1984): `x`=55, `f`=35, `r`=21, `v`=53.

```
hufnix davhar niev caif kax
af gov diex caf
```

**Toned IPA**: Chao digits, superscripts or Chao letters, one tone per syllable; a syllable
without a tone is read as `T0`.

```
xu21 ni21        xu²¹ ni²¹        xu˨˩ ni˨˩
```

Syllable splitting, initial/final parsing and tone-notation normalisation are delegated to
**`tujia-nlp`** (`tujia_nlp.corpus`, `tujia_nlp.tones`). This package only keeps the table
that the checkpoint was trained on (41 symbols, `-ng` finals as `aŋ/eŋ/iŋ/oŋ`, `z/c/s/r + i → ɿ`)
and the rule that appends one tone token per syllable. Chinese characters are not supported.

## Pre- and post-processing

Text side: notation normalisation → syllable split and initial/final parsing (`tujia-nlp`) →
IPA → tone token → unknown symbols dropped and counted (never a silent `KeyError`) → empty
input raises.

Waveform side (`postprocess()`): trim leading/trailing silence (−40 dBFS relative to peak,
30 ms margin) → peak normalise to −1 dBFS → 10 ms fade in/out.

## Evaluation

| Metric | v0.2 | v0.3 |
|---|---|---|
| Phone error rate, 40 sentence probes (synthesized) | 0.784 | **0.690** (median) |
| Phone error rate, same probes (human audio) | 0.567 | 0.567 |
| Validation mel loss | 0.5108 | **0.4523** |

Same 40 sentence probes for both versions: synthesize, then send through the Tujia ASR and
compare against the expected IPA phone string. The human row is the ASR's noise floor on
the original recordings, so only the gap between the rows is meaningful.

## Known limitations

1. **Tone is approximate.** Tone tokens are trained from corpus annotation; sandhi and
   emphatic lengthening are not modelled.
2. **Short single-syllable words are the weakest.** They are most sensitive to prosody
   and to the 16 ms frame rate.
3. **No prosody control.** No SSML, breaks, or emphasis; `length_scale` is the only knob.
4. **One speaker only.** No voice conversion, no cloning, no multi-speaker selection.
5. **Plosive bursts are smeared.** The 16 kHz / 256-hop configuration gives 16 ms per
   frame, which is coarser than a stop burst; synthetic audio is brighter than real
   recordings (high-band energy share 0.177 vs 0.104) while bursts are less dense.
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
| v0.3 | 6.40 h / 3,958 clips, unified to badou | Longer corpus, deterministic duration, toned-IPA input |
