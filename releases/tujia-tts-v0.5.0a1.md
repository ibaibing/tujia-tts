# tujia-tts v0.5.0a1 (preview)

Released 2026-11-28. Fourth public release, **alpha preview**.

This is not a stable release. Training is still running (400-epoch schedule, epoch ~175 at
packaging time); the package ships **epoch 162**, and the duration predictor still drifts on
some sentence patterns (see *Known issues*). Version is `0.5.0a1` on PyPI so that a stable
`0.5.0` can follow without renumbering.

## Model

| Item | Value |
|---|---|
| Weights | `vits_tujia-v0.5.onnx` (ONNX opset 15, IR 8) + `vits_tujia-v0.5.onnx.json` |
| Size | 63,354,317 bytes |
| SHA256 | `ee2f1b16c45d4d411b4f0739cf7850879bae69cae4d7983de89a7b86f436c67f` |
| Sample rate | 16,000 Hz, mono |
| Symbols | 40 (34 phones + `T0`–`T4` + 4 control tokens) |
| Speakers | 1 — **badou** only |
| Determinism | random layers seeded (`seed=42`), same text → same wav hash |

## Provenance

v0.5 is **trained from scratch**, not a fine-tune. Unlike v0.2–v0.4, which used a single
speaker's recordings, this run starts from the rebuilt multi-source corpus:

| Step | Effect |
|---|---|
| Sources | 17 speakers from the v18 rebuild |
| Voice conversion | every clip converted to the **consented `badou` timbre** |
| EQ matching | source-to-target spectral matching after VC |
| Re-segmentation | shorter utterances, 9,757 clips / 4.655 h |
| Unmarked tone | labelled `T3` (21) |

The model therefore never sees the original timbres and cannot reproduce them. Training
audio is not distributed.

## What changed from v0.4

| Item | v0.4 | v0.5.0a1 |
|---|---|---|
| Clips / hours | 3,881 / 6.47 h | 9,757 / 4.66 h |
| Source speakers | 1 | 17, all VC'd to `badou` |
| Initialisation | fine-tune of v0.3 | from scratch |
| Symbols | 41 | **40** (retroflex stop `ʈ` dropped) |
| Validation mel loss | 0.4195 | 0.4700 (epoch 162) |
| ONNX size | 63,350,962 B | 63,354,317 B |

**The two validation losses are not comparable**: different split, different symbol table,
different corpus construction. Lower is not claimed here.

## Verification

```
$ tujia-tts --text "af gov diex caf" -o a.wav
text   : af gov diex caf
ids    : 37
unknown: 0 (>0 means some syllables/symbols are not in the phoneme table)
audio  : 1.55s @ 16000 Hz, peak -1.0 dBFS -> a.wav

$ shasum -a 256 a.wav
17e00a118ec5d51873b94b610c08d12934de9b060b19a0adfb34ef342d63b359  a.wav
```

Three separate processes produced the same hash. The graph still has exactly three inputs:

```
$ python3 -c "import onnx; m=onnx.load('vits_tujia-v0.5.onnx'); print([i.name for i in m.graph.input])"
['input', 'input_lengths', 'scales']
```

## Known issues

- **Sentence-level duration drift.** On a fixed 53-line test text, epoch 162 is 20 % longer
  than epoch 152 of the same run (median line ×1.20, worst line ×2.24). A few sentence
  patterns are stretched; it is not a global slowdown. This is the main reason for `a1`.
- **Converted timbre.** All training audio is VC output; very breathy or very young source
  voices may carry artefacts through conversion.
- **Phoneme table shrank.** `vits_tujia-v0.4.onnx.json` cannot be used with this model.
  Unknown symbols (including `ʈ`) are dropped and counted instead of raising.
- Tone is approximate; sandhi and emphatic lengthening are not modelled.
- Single-syllable words remain the weakest.
- Round-trip ASR and native-listener tone checks have **not** been run for this preview.

## Upgrade notes

- `pip install tujia-tts==0.5.0a1` (pre-release, exact pin required).
- The Python API is unchanged: `synthesize(text, notation=..., length_scale=...)`.
- If you need the 41-symbol behaviour, stay on `0.4.0`.
