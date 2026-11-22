# tujia-tts v0.4

Released 2026-11-22. Third public release.

## Model

| Item | Value |
|---|---|
| Weights | `vits_tujia-v0.4.onnx` (ONNX opset 15) + `vits_tujia-v0.4.onnx.json` |
| Size | 63,350,962 bytes |
| SHA256 | `4f2f17450f39e596e440f559e6d0fbab9355099d633bd183ab130597943dd6f0` |
| Sample rate | 16,000 Hz, mono |
| Symbols | 41 (IPA phones + `T0`–`T4`) |
| Speakers | 1 — **badou** only |

## Provenance

v0.4 is a **fine-tune of v0.3**, not a model trained from scratch. Starting from the v0.3
checkpoint (`validation mel loss 0.4523`), it was trained for 60 epochs at learning rate
5e-5 on 3,881 clips / 6.47 h. The released checkpoint is epoch 20 (validation mel loss
0.4195 on a fixed train/val split).

The corpus is the v0.3 corpus after audio repair:

| Step | Effect |
|---|---|
| Trailing silence | 150 ms appended to every clip that ended in speech |
| Leading silence | 30 ms appended when the first phone touched the clip edge |
| Peak | normalised to −3 dBFS |
| Dropped | 72 clips with clipping above 3 % |
| Unmarked tone | labelled `T3` (21) instead of `T0` (5.75 % of syllables) |

Training data is not distributed.

## What changed from v0.3

| Item | v0.3 | v0.4 |
|---|---|---|
| Data | 3,958 clips / 6.40 h | 3,881 clips / 6.47 h (silence-padded) |
| Initialisation | from scratch | fine-tuned from v0.3 |
| Validation mel loss | 0.4523 | **0.4195** |
| ASR error rate, 100 held-out sentences (synthesized) | 0.973 | **0.972** |
| ASR error rate, same sentences (human) | 0.805 | 0.804 |
| Median syllable duration (human: 222 ms) | 185 ms | **221 ms** |
| Energy in the last 100 ms (median, relative to clip) | 0.237 | **0.000** |
| Unmarked syllables | `T0` | `T3` (21) |

The two visible gains are prosodic rather than lexical: v0.3 spoke about 17 % faster than
the human recordings and ended on a hard cut, while v0.4 matches the human syllable
duration and closes on real silence. Intelligibility, measured by round-trip ASR, is
unchanged.

Forced-alignment breakdown on the same 100 sentences (onset presence, human in brackets):
aspirated 0.556 → **0.634** (0.802), unaspirated 0.793 → **0.814** (0.887), fricative
0.465 → 0.455 (0.573), liquid 0.741 → 0.706 (0.824), nasal 0.765 → 0.658 (0.872).
Stops improve; sonorants give back a little.

## Verification

```
$ tujia-tts --text "af gov diex caf" -o a.wav
unknown: 0 (>0 means some syllables/symbols are not in the phoneme table)
audio  : 1.85s @ 16000 Hz, peak -1.0 dBFS -> a.wav

$ shasum -a 256 a.wav
8bb65cfec903bb96ce22bbae8efb180f8317caafd9f4f8b8540356792c3856e9  a.wav
```

Three separate processes produced the same file hash. The ONNX graph still has three
inputs:

```
$ python3 -c "import onnx; m=onnx.load('vits_tujia-v0.4.onnx'); print([i.name for i in m.graph.input])"
['input', 'input_lengths', 'scales']
```

Round-trip ASR on the 100 held-out sentences gives 1.001 through the ONNX export versus
0.972 on the PyTorch checkpoint; the difference comes from the seeded duration draw and
export numerics, and is inside the per-item noise of the probe.

## Known issues

- **Sonorants regressed slightly.** Nasal and lateral onsets are less often present than
  in v0.3 (see the alignment numbers above). The tail-silence fix traded a little of this.
- Tone sandhi and emphatic lengthening are not modelled.
- Plosive bursts are smeared: 16 ms per frame is coarser than a stop burst, so synthetic
  audio is brighter than real recordings.
- Single-syllable words remain the most fragile.
- The 41-symbol phoneme table is unchanged from v0.3, but unmarked syllables now map to
  `T3`; v0.3 `.onnx.json` files are not interchangeable with this model.
- The package trims trailing silence to a 30 ms margin on purpose; pass `--no-trim` to keep
  the full generated tail.
