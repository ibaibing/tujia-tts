---
title: Tujia TTS
emoji: 🔊
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.29.1
app_file: app.py
pinned: false
license: mit
short_description: Tujia text to speech (Ye pinyin / IPA), single badou voice
---

# 土家语语音合成台

Ye 拼音或带调 IPA → 16 kHz 语音，单音色 **badou**。

- 模型：`TujiaNLP/tujia-tts-v0.3`（VITS，ONNX，63 MB）
- 代码：https://github.com/ibaibing/tujia-tts
- 安装：`pip install tujia-tts`

## 能做什么

| 输入 | 例子 |
|---|---|
| Ye 拼音 | `hufnix davhar niev caif kax`、`af gov diex caf` |
| 带调 IPA | `xu21 ni21`、`xu²¹ ni²¹`、`xu˨˩ ni˨˩` |
| 数字调 Ye | `bi2zi1ka3` |

记法默认自动判别，也可以在界面上强制 `ye` / `ipa`。汉字不支持，会被忽略。

## 已知限制

1. **不是 piper 标准语音**：音素表含双字符调 token（`T0`–`T4`），须用自带前端。
2. **声调近似**：连读变调与强调拉长未建模。
3. **单音节词最脆**：短词受韵律与 16 ms 帧率影响最大。
4. **爆破音瞬态被抹平**：16 kHz / 256 hop 的帧率比塞音爆发段粗，合成音偏亮。
5. 模型为研究预览，正式使用（出版、教学材料）前请由母语者校对。

## 许可边界

- 本创空间的代码为 **MIT**。
- 模型权重仅供**研究用途**，不授予训练录音、转写文本或说话人声音的任何权利，详见主仓库 `NOTICE`。
- 合成音频不得被表述为真人录音；克隆任何说话人的声音都需要该说话人的明确同意。

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

CPU 即可运行；单次合成约 1–3 秒（含 ONNX 会话初始化）。
