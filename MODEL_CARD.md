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

# Model Card — tujia-tts v0.5.0a1 (preview)

## Overview

`vits_tujia-v0.5` is a single-speaker Tujia text-to-speech model. Input is **Ye pinyin**
(the Ye De-shu transcription, tone letters `x / f / r / v`) or **toned IPA**, output is
**16 kHz mono** speech in **one voice only: badou**.

There is no speaker conditioning: the model's `SynthesizerTrn` is single-speaker, so the
ONNX graph has exactly three inputs (`input`, `input_lengths`, `scales`) and **no `emb_g`
/ `sid` channel**. Switching the voice requires switching the model file.

> **Preview release.** Training is still running (400-epoch schedule); this package ships
> epoch 162. Loss and prosody can still move, and the duration issue listed under *Known
> issues* is the main reason this is marked `a1` rather than final.

## Model

| Item | Value |
|---|---|
| Weights | `vits_tujia-v0.5.onnx` (ONNX opset 15, IR 8) + `.onnx.json` |
| Size | 63,354,317 bytes |
| SHA256 | `ee2f1b16c45d4d411b4f0739cf7850879bae69cae4d7983de89a7b86f436c67f` |
| Sample rate | 16,000 Hz, mono |
| Symbols | 40 (34 phones + `T0`–`T4` + 4 control tokens) |
| Speakers | 1 — **badou** only |
| Backbone | VITS, hop 256, upsample 8/8/4 |

## Training data

| Item | Value |
|---|---|
| Clips | 9,757 |
| Duration | 4.655 h |
| Source speakers | 17, **all converted to the badou timbre** |
| Segmentation | re-cut into shorter utterances (median well under v0.4) |

This is the important difference from earlier releases: the source corpus is multi-speaker,
but every clip was passed through voice conversion to the **consented `badou` voice** and
then EQ-matched before training. The model therefore never sees the raw timbre of the other
speakers, and it cannot reproduce their voices. Clips are not distributed.

## Input format

```
hufnix davhar niev caif kax      Ye pinyin, tone letters      -> 你好，慢慢走
xu21 ni21        xu²¹ ni²¹        xu˨˩ ni˨˩                  toned IPA
```

Syllable splitting, initial/final parsing and tone-notation normalisation are delegated to
**`tujia-nlp`** (`tujia_nlp.corpus`, `tujia_nlp.tones`). This package keeps the table the
checkpoint was trained on (40 symbols, `-ng` finals as `aŋ/eŋ/iŋ/oŋ`, `z/c/s/r + i → ɿ`)
and the rule that appends one tone token per syllable. Chinese characters are not supported.

Symbols missing from the table (for example the retroflex stop `ʈ`, which v0.4 had and v0.5
does not) are dropped and counted in `n_unknown` instead of raising.

## Pre- and post-processing

Text side: notation normalisation → syllable split and initial/final parsing (`tujia-nlp`) →
IPA → tone token → unknown symbols dropped and counted → empty input raises.

Waveform side (`postprocess()`): trim leading/trailing silence (−40 dBFS relative to peak,
30 ms margin) → peak normalise to −1 dBFS → 10 ms fade in/out.

## Evaluation

| Metric | v0.4 | v0.5.0a1 |
|---|---|---|
| Clips / hours | 3,881 / 6.47 h | 9,757 / 4.66 h |
| Symbols | 41 | 40 |
| Validation mel loss | 0.4195 | **0.4700** (epoch 162) |
| Round-trip ASR probe | 0.972 | not run yet |
| Median syllable duration vs human | 221 ms (human 222 ms) | see known issues |

**Do not compare the two `val_mel` numbers.** v0.4 was fine-tuned on a different validation
split with a 41-symbol inventory; 0.4195 and 0.4700 are not on the same scale. The round-trip
probe and duration statistics have not been re-run for this preview.

## Known issues

1. **Sentence-level duration drift.** Compared with epoch 152 of the same run, this
   checkpoint is 20 % longer overall on the fixed 53-line lyric test, with the median line
   1.20× and some lines up to 2.24×. Not a global speed change: the duration predictor is
   unstable on a few sentence patterns. Listen for dragging before deploying.
2. **Tone is approximate.** Tone tokens are trained from corpus annotation; sandhi and
   emphatic lengthening are not modelled.
3. **Vocal timbre is converted, not recorded.** All training audio is VC output in the badou
   timbre; very breathy or very young source voices may have artefacts that survived VC.
4. **Single-syllable words remain the weakest.** Most sensitive to prosody and to the 16 ms
   frame rate.
5. **No prosody control.** No SSML, breaks, or emphasis; `length_scale` is the only knob.
6. **Phoneme table changed.** `.onnx.json` files from v0.4 are **not** interchangeable with
   this model (41 → 40 symbols).
7. **Preview.** Training continues; do not pin production systems to `0.5.0a1`.

## Intended use

Suitable: research on low-resource TTS, community demo material reviewed by native
speakers, and prototyping Tujia audio interfaces.

Not suitable: publication or teaching material without native-speaker review, any claim
that the output is a real person's recording, or commercial redistribution.

## Licensing and ethics

Code is MIT. Weights are research-use only under `NOTICE`. The training audio is voice
converted into the consented `badou` timbre; the original speakers' voices are not
reproduced by this model. Commercial use or redistribution still requires a rights review.
Tujia is endangered — outputs should be reviewed by native speakers before community or
educational use.

## Version history

| Version | Data | Notes |
|---|---|---|
| v0.1 | 1.87 h / 2,390 clips, male teacher | Failed intelligibility probe; not released |
| v0.2 | 4.10 h / 3,403 clips, unified to badou | First public release |
| v0.3 | 6.40 h / 3,958 clips, unified to badou | Longer corpus, deterministic duration, toned-IPA input |
| v0.4 | 6.47 h / 3,881 clips, unified to badou, trailing silence padded | Fine-tune of v0.3: human-like syllable timing, no abrupt clip endings, unmarked syllables read as 21 |
| v0.5.0a1 | 4.66 h / 9,757 clips, 17 speakers VC'd to badou, re-cut | Trained from scratch; 40-symbol table (ʈ removed); preview with duration drift |
