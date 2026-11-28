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

from ipa_kb import IPA_CSS, IPA_HTML, IPA_JS
from demo_nav import NAV_CSS, nav_html

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

from tujia_tts import synthesize as tts_synthesize, write_wav  # noqa: E402

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
        audio, sr, n_unknown, n_ids = tts_synthesize(
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


def synthesize(text: str, notation: str = "auto", length_scale: float = 1.0):
    """把土家语文本合成为语音（单说话人 badou），返回 wav 音频与状态说明。

    只支持土家语 Ye 拼音或带调 IPA，汉字会被忽略。同一句的时长是固定的，
    语速由 length_scale 控制；音频是 16 kHz 单声道 wav。

    Args:
        text: 要合成的文本，Ye 拼音（如 "hufnix davhar niev caif kax"）或带调 IPA（如 "xu21 ni21"）。
        notation: 记法，"auto" 自动判断（默认），"ye" 强制按 Ye 拼音，"ipa" 强制按带调 IPA。
        length_scale: 语速系数，1.0 为正常，大于 1 更慢，取值 0.7–1.4。

    Returns:
        (wav 文件, 状态文本：音节 id 数、时长、未识别音节数)
    """
    return _fmt(text, notation, length_scale)


_GR_MAJOR = int(gr.__version__.split(".")[0])
# gradio 6 把 css 从 Blocks 移到 launch；4/5 仍在 Blocks 上
_BLOCKS_KW = {} if _GR_MAJOR >= 6 else {"css": CSS + IPA_CSS + NAV_CSS}
_LAUNCH_KW = {"css": CSS + IPA_CSS + NAV_CSS} if _GR_MAJOR >= 6 else {}
if _GR_MAJOR >= 5:
    _LAUNCH_KW["mcp_server"] = True


def build():
    with gr.Blocks(title="土家语语音合成", **_BLOCKS_KW) as demo:
        gr.HTML(nav_html("tts"))
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
            elem_id="ipa-input",
        )
        with gr.Accordion("输入键盘（Ye / IPA / 语音）", open=False) as kb_acc:
            gr.HTML(IPA_HTML)
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

        btn.click(_fmt, [txt, notation, length_scale], [out, status], api_name=False)
        txt.submit(_fmt, [txt, notation, length_scale], [out, status], api_name=False)
        # MCP / HTTP API 入口（不可见）：把合成暴露成具名端点 synthesize
        api_txt = gr.Textbox(visible=False)
        api_notation = gr.Radio(["auto", "ye", "ipa"], value="auto", visible=False)
        api_ls = gr.Slider(0.7, 1.4, value=1.0, step=0.05, visible=False)
        api_btn = gr.Button(visible=False)
        api_audio = gr.Audio(type="filepath", visible=False)
        api_status = gr.Textbox(visible=False)
        api_btn.click(synthesize, [api_txt, api_notation, api_ls], [api_audio, api_status],
                      api_name="synthesize")
        demo.load(None, None, None, js=IPA_JS)
        if hasattr(kb_acc, "expand"):
            kb_acc.expand(None, None, None, js=IPA_JS)
    return demo


if __name__ == "__main__":
    build().launch(server_name="0.0.0.0",
                   server_port=int(os.environ.get("PORT", 7860)),
                   **_LAUNCH_KW)
