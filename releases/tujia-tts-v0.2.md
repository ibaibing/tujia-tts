# tujia-tts v0.2

Released 2026-11-17. First public release.

## Model

| Item | Value |
|---|---|
| Weights | `vits_tujia-v0.2.onnx` (ONNX opset 15) + `vits_tujia-v0.2.onnx.json` |
| Size | 63,350,929 bytes |
| SHA256 | see `SHA256SUMS` in the release assets |
| Sample rate | 16,000 Hz, mono |
| Symbols | 41 (IPA phones + `T0`–`T4`) |
| Speakers | 1 — **badou** only |

## Provenance

Trained on 3,403 clips / 4.10 h from four sources, all converted to the `badou` timbre
(validation mel loss 0.5108 at the released checkpoint). Training data is not distributed.

## What changed from v0.1

| Item | v0.1 | v0.2 |
|---|---|---|
| Data | 1.87 h / 2,390 clips / one source | 4.10 h / 3,403 clips / four sources |
| Speaker | male teacher | badou (unified) |
| Phone inventory | contains `õ`, no `ɣ` | contains `ɣ`, no `õ` (**not interchangeable**) |
| Post-processing | none | trim silence, peak −1 dBFS, 10 ms fade |
| Unknown symbols | `KeyError` | dropped and counted |

The phoneme id table differs from v0.1; `.onnx.json` files are not interchangeable.

## Verification

```
$ python3 -c "import onnx; m=onnx.load('vits_tujia-v0.2.onnx'); print([i.name for i in m.graph.input])"
['input', 'input_lengths', 'scales']
```

No `sid` / `emb_g`: the single-speaker model has no speaker channel.

```
$ tujia-tts --text "af gov diex caf" -o a.wav
ids    : 19
unknown: 0
audio  : 1.36s @ 16000 Hz, peak -1.0 dBFS -> a.wav
```

## Known issues

- Stochastic duration predictor (`/dp/RandomNormalLike`) makes duration vary across
  processes; pin the node seed or fix `length_scale` if output must be reproducible.
- Tone sandhi and emphatic lengthening are not modelled.
- Single-syllable words are the most fragile.
