# Examples — v0.3 sample outputs

Three utterances synthesized by `vits_tujia-v0.3` at default settings
(`length_scale 1.0`, `noise_scale 0.667`, `noise_w 0.8`, post-processing on).
16 kHz mono, peak −1 dBFS.

| File | Input (Ye pinyin) | Meaning | Duration |
|---|---|---|---|
| [line_001.wav](line_001.wav) | `huf nix dar har niex caif kax` | 大家都过好日子 | 1.41 s |
| [line_002.wav](line_002.wav) | `lox bax diex kax tiex bev` | 阿哥把犁搬 | 2.30 s |
| [line_003.wav](line_003.wav) | `mar maf diex cer kur cev` | 阿妹绩麻线 | 2.24 s |

Reproduce any of them with:

```bash
tujia-tts --text "huf nix dar har niex caif kax" -o line_001.wav
```

Output is deterministic: the duration predictor is seeded at export, so the same text
produces the same file in every process. Use `--length-scale 1.1` for slightly slower
speech.

These are the first three lines of 大家都过好日子, used across releases as a listening
check. Recordings, transcripts and the speaker's voice are not distributed; see
[../NOTICE](../NOTICE).
