"""三个演示页之间的互跳入口（页面顶部的一排胶囊链接）。

每个 Space 是独立仓库，所以这个文件在 tujia-asr / tujia-tts / tujia-llm 的
space/ 目录各放一份，内容一致；改的时候三处同步。
"""

NAV_CSS = """
.demo-nav{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}
.demo-nav a{display:inline-block;padding:5px 14px;border:1px solid #cfe3dc;border-radius:16px;
  background:#fff;color:#2f7a67;font-size:13px;text-decoration:none;line-height:1.4}
.demo-nav a:hover{background:#eef6f3}
.demo-nav a.on{background:#2f7a67;border-color:#2f7a67;color:#fff;pointer-events:none}
"""

ITEMS = [
    ("asr", "语音转写", "https://modelscope.cn/studios/TujiaNLP/tujia-asr-demo"),
    ("tts", "语音合成", "https://modelscope.cn/studios/TujiaNLP/tujia-tts-demo"),
    ("llm", "大模型问答", "https://modelscope.cn/studios/TujiaNLP/tujia-llm-demo"),
]


def nav_html(current: str) -> str:
    parts = []
    for key, label, url in ITEMS:
        cls = ' class="on"' if key == current else ""
        parts.append(f'<a{cls} href="{url}" target="_blank" rel="noopener">{label}</a>')
    return '<div class="demo-nav">' + "".join(parts) + "</div>"
