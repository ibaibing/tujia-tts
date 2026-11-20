#!/usr/bin/env python3
"""Tujia TTS demo -- Gradio app for Hugging Face Spaces / ModelScope Studios.

The model is not run in the browser: `tujia-tts` ships a 63 MB ONNX model that
is executed on the container CPU. Input may be Ye pinyin or toned IPA; the
notation is detected automatically unless the user forces one.

Layout notes
------------
Most visitors open these links on a phone, so the UI keeps a single column,
44 px+ touch targets, 16 px body text (prevents iOS zoom-on-focus) and no
hover-only affordances. The generated audio is returned as a file path so
Safari can play it after the tap that produced it.
"""
from __future__ import annotations

import os
import tempfile

import gradio as gr

# Gradio 4.44 / gradio_client 1.x schema bug: Audio and File components declare
# `additionalProperties` as a bool, so get_api_info() raises TypeError, `/`
# returns 500 and the app never becomes reachable. The UI and events do not
# depend on that document, so fall back to an empty one. Patched defensively so
# newer Gradio versions (where the bug is fixed or the method moved) are untouched.
import gradio.blocks as _gr_blocks  # noqa: E402

if hasattr(_gr_blocks.Blocks, "get_api_info"):
    _orig_api_info = _gr_blocks.Blocks.get_api_info

    def _safe_api_info(self, *args, **kwargs):
        try:
            return _orig_api_info(self, *args, **kwargs)
        except TypeError:
            return {"named_endpoints": {}, "unnamed_endpoints": {}}

    _gr_blocks.Blocks.get_api_info = _safe_api_info

from tujia_tts import synthesize, write_wav  # noqa: E402

EXAMPLES = [
    ["hufnix davhar niev caif kax", "你好吗"],
    ["pofgav", "你好"],
    ["lafgof", "什么"],
    ["mor", "名字 / 叫"],
    ["af gov diex caf", "我很好"],
    ["xu21 ni21", "IPA 写法"],
]

CSS = """
.gradio-container { max-width: 760px !important; margin: 0 auto !important; }
footer { display: none !important; }
#title h1 { font-size: 22px; margin-bottom: 2px; }
#title p { font-size: 14px; color: #555; margin-top: 0; }
#out audio { width: 100% !important; }
@media (max-width: 640px) {
  .gradio-container { padding: 8px !important; }
  #title h1 { font-size: 20px; }
  textarea, input { font-size: 16px !important; }
  .gr-button { min-height: 44px; font-size: 16px; }
}
"""


def _fmt(text: str, notation: str, length_scale: float):
    """Synthesize one utterance and return (wav path, status markdown)."""
    text = (text or "").strip()
    if not text:
        return None, "请输入 Ye 拼音或带调 IPA。"
    try:
        audio, sr, n_unknown, n_ids = synthesize(
            text, notation=notation, length_scale=float(length_scale))
    except ValueError as exc:
        return None, f"无法合成：{exc}"
    except Exception as exc:                      # noqa: BLE001
        return None, f"合成失败：{type(exc).__name__}: {exc}"

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    write_wav(path, audio, sr)

    dur = len(audio) / sr
    flag = "" if n_unknown == 0 else f" · **{n_unknown} 个音节未识别**"
    return path, f"`{n_ids}` 个 id · {dur:.2f} 秒 · 16 kHz{flag}"


def build():
    with gr.Blocks(css=CSS, title="土家语语音合成") as demo:
        with gr.Column(elem_id="title"):
            gr.Markdown(
                "# 土家语语音合成 · tujia-tts\n"
                "输入 **Ye 拼音**（`hufnix davhar niev caif kax`）或**带调 IPA**（`xu21 ni21`）。"
                "单音色：badou。"
            )

        txt = gr.Textbox(
            label="文本",
            placeholder="例如 hufnix davhar niev caif kax",
            lines=2,
        )
        with gr.Row():
            notation = gr.Radio(["auto", "ye", "ipa"], value="auto", label="记法")
            length_scale = gr.Slider(0.7, 1.4, value=1.0, step=0.05,
                                     label="语速（>1 更慢）")
        btn = gr.Button("合成", variant="primary")
        out = gr.Audio(label="合成结果", type="filepath", elem_id="out")
        status = gr.Markdown("")

        gr.Examples(examples=EXAMPLES, inputs=[txt], label="示例")

        gr.Markdown(
            "> 只支持土家语 Ye 拼音 / IPA，**汉字会被忽略**。"
            "同一句的时长是固定的；要调语速请用滑块。"
            "模型为研究预览，正式使用前请由母语者校对。"
        )

        btn.click(_fmt, [txt, notation, length_scale], [out, status])
        txt.submit(_fmt, [txt, notation, length_scale], [out, status])
    return demo


if __name__ == "__main__":
    build().launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
