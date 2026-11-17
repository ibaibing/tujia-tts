# -*- coding: utf-8 -*-
"""tujia-tts — 土家语语音合成（Ye 拼音 → 16 kHz 波形）。

发布版本与音色：v0.2，单说话人 **badou**。
"""
from .synth import (  # noqa: F401
    DEFAULT_ONNX,
    DEFAULT_VOICE,
    postprocess,
    synthesize,
    write_wav,
)
from .ye_phonemes import tokenize_ye, to_ids  # noqa: F401

__version__ = "0.2.0"
__all__ = [
    "synthesize", "postprocess", "write_wav", "tokenize_ye", "to_ids",
    "DEFAULT_ONNX", "DEFAULT_VOICE", "__version__",
]
