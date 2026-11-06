# tujia-tts

Release hub for text-to-speech models of **Northern Tujia (Longshan Miaoertan standard pronunciation)**.

This repository distributes synthesis checkpoints, inference scripts, and the intelligibility
evaluation protocol. Data production, training and experiments live in
[tujia-tts-lab](https://github.com/ibaibing/tujia-tts-lab).

> **Status: no public release yet.**
> The first end-to-end model (`vits_tujia-v1`, 2,390 clips / 1.87 h, val mel 0.450) was trained
> and is **not usable**: an intelligibility probe (19 words) measured a median speaker similarity
> of 0.40 on real audio versus 0.00–0.20 on synthesized audio. Shipping it would do more harm
> than good. The next attempt depends on the corpus v0.1/v0.2 rebuild.

## Planned releases

| Version | Data | Engine | Gate | Status |
| --- | --- | --- | --- | --- |
| v1 | 2,390 clips / 1.87 h | VITS | intelligibility | Failed the probe, not released |
| v2 | corpus v0.1 (single-speaker clean slice) | TBD | median similarity ≥ 0.5, tone acceptable to native listeners | Planned |
| v3 | corpus v0.2 | TBD | + cross-speaker generalisation | Planned |

A version is released only if it passes the intelligibility gate. Weights are never released
on the basis of training loss alone.

## What will be here

```
README.md              this file
LICENSE                MIT (code)
NOTICE                 usage boundaries for weights
requirements.txt       inference dependencies
synth.py               text → waveform entry point
phones/                IPA inventory and text front-end rules
docs/protocol.md       intelligibility and tone evaluation protocol
docs/usage.md          install, download, sample-rate and device notes
releases/              versioned archives + SHA256SUMS
```

## Evaluation

- **Intelligibility**: forced-choice listening on 19 probe words plus a synthesized-vs-real
  similarity sweep; the primary number is median speaker similarity.
- **Tone**: native-listener acceptance of the four tones `21 / 35 / 53 / 55`.
- **Robustness**: same sentence across speakers; refusal to score on unseen phonotactics.

Protocol details will be published with the first passing release.

## Related

| Repository | Role |
| --- | --- |
| [TujiaNLP](https://github.com/ibaibing/TujiaNLP) | Corpus, collection standards, licensing |
| [tujia-tts-lab](https://github.com/ibaibing/tujia-tts-lab) | Training and experiments |
| [tujia-asr](https://github.com/ibaibing/tujia-asr) | The reverse direction: speech → syllables |
| [tujia-llm](https://github.com/ibaibing/tujia-llm) | Language model layer |

## License

- Code: MIT
- Model weights: research use only; no rights to recordings, transcripts, or speaker voices
