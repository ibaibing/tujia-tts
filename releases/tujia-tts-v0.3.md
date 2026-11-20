# tujia-tts v0.3

Released 2026-11-20. Second public release.

## Model

| Item | Value |
|---|---|
| Weights | `vits_tujia-v0.3.onnx` (ONNX opset 15) + `vits_tujia-v0.3.onnx.json` |
| Size | 63,350,962 bytes |
| SHA256 | `e5fb0a426f77c353dca887e04ed09c1d5989e2be24dec5cf8a3d03fd4e12c74a` |
| Sample rate | 16,000 Hz, mono |
| Symbols | 41 (IPA phones + `T0`–`T4`) |
| Speakers | 1 — **badou** only |

## Provenance

Trained on 3,958 clips / 6.40 h, all timbre-converted to **badou** (validation mel loss
0.4523 at the released checkpoint). Training data is not distributed.

## What changed from v0.2

| Item | v0.2 | v0.3 |
|---|---|---|
| Data | 4.10 h / 3,403 clips | 6.40 h / 3,958 clips |
| Validation mel loss | 0.5108 | 0.4523 |
| Phone error rate, 40 sentence probes (synthesized) | 0.784 | 0.690 |
| Phone error rate, same probes (human audio) | 0.567 | 0.567 |
| Duration | varies across processes (1.2–2.8 s for one sentence) | **deterministic** |
| Input notation | Ye pinyin | Ye pinyin **and** toned IPA |
| Syllable parsing | bundled table | delegated to `tujia-nlp` |

The duration fix is an export-time change: the stochastic duration predictor's
`RandomNormalLike` node is seeded, so every process draws the same noise. The exported
graph still has three inputs:

```
$ python3 -c "import onnx; m=onnx.load('vits_tujia-v0.3.onnx'); print([i.name for i in m.graph.input])"
['input', 'input_lengths', 'scales']
```

## Verification

```
$ tujia-tts --text "af gov diex caf" -o a.wav
ids    : 37
unknown: 0
audio  : 1.49s @ 16000 Hz, peak -1.0 dBFS -> a.wav

$ shasum -a 256 a.wav
62d37aca1c2c223b2bc549a1dd5d14d53023b8ec721c63192d8b86315229f6f4  a.wav
```

Running the same command in three separate processes produced the same file hash.

```
$ tujia-tts --text "xu21 ni21" -o b.wav --notation ipa
ids    : 17
unknown: 0
audio  : 0.95s @ 16000 Hz, peak -1.0 dBFS -> b.wav
```

## Known issues

- Tone sandhi and emphatic lengthening are not modelled.
- Plosive bursts are smeared: 16 ms per frame is coarser than a stop burst, so synthetic
  audio is brighter than real recordings (high-band energy share 0.177 vs 0.104).
- Single-syllable words remain the most fragile.
- The 41-symbol phoneme table is unchanged from v0.2; `.onnx.json` files from v0.1 are not
  interchangeable.
