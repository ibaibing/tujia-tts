# -*- coding: utf-8 -*-
"""tujia-tts: Tujia speech synthesis (Ye pinyin / IPA -> 16 kHz waveform).

Release v0.4, single speaker: **badou**.
"""
from .frontend import (  # noqa: F401
    detect_notation,
    to_ids,
    tokenize,
    tokenize_ipa,
    tokenize_ye,
)
from .synth import (  # noqa: F401
    DEFAULT_ONNX,
    DEFAULT_VOICE,
    postprocess,
    synthesize,
    write_wav,
)

__version__ = "0.4.0"
__all__ = [
    "synthesize", "postprocess", "write_wav",
    "tokenize", "tokenize_ye", "tokenize_ipa", "to_ids", "detect_notation",
    "DEFAULT_ONNX", "DEFAULT_VOICE", "__version__",
]
