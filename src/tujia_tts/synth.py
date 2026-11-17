# -*- coding: utf-8 -*-
"""土家语 VITS（v0.2）本地合成：Ye 拼音 → 16 kHz 语音。

用法：
  python3 synth.py --text "hufnix davhar niev caif kax" -o out.wav
  python3 synth.py --text "af gov diex caf" -o a.wav --length-scale 1.0

输入必须是 **Ye 拼音**（如 af gov diex caf），不是汉字。
依赖：onnxruntime、numpy；模型与音素表随本目录一起分发。

预处理：语料记法归一（借词星号 / 数字调 / 说话人标签 / 音节末 y→v）→ 音节切分
→ 声韵母转 IPA → 每音节补调 token → 未知符号丢弃并计数（不静默崩溃）。
后处理：掐首尾静音 → 峰值归一（默认 −1 dBFS）→ 10 ms 淡入淡出（去爆音）。
"""
import argparse
import json
import os
import re
import wave

import numpy as np
import onnxruntime as ort

try:                       # 作为 tujia_tts 包的一部分被导入
    from .ye_phonemes import to_ids, tokenize_ye
except ImportError:        # 直接跑 python3 synth.py
    from ye_phonemes import to_ids, tokenize_ye

_CJK_RE = re.compile(r"[\u3400-\u9fff]")

HERE = os.path.dirname(os.path.abspath(__file__))
# 直接使用时模型与代码同目录；装成包后模型在 tujia_tts/data/ 下
_DATA = os.path.join(HERE, "data")
if os.path.exists(os.path.join(_DATA, "vits_tujia-v0.2.onnx")):
    HERE = _DATA
DEFAULT_ONNX = os.path.join(HERE, "vits_tujia-v0.2.onnx")
DEFAULT_VOICE = os.path.join(HERE, "vits_tujia-v0.2.onnx.json")

TRIM_THR_DB = -40.0     # 首尾静音阈值（相对峰值）
TRIM_MARGIN = 0.03      # 掐静音后保留的余量（秒）
TARGET_DBFS = -1.0      # 峰值归一目标
FADE_MS = 10.0          # 淡入淡出时长


def trim_silence(x, sr, thr_db=TRIM_THR_DB, margin=TRIM_MARGIN):
    """按峰值相对阈值掐掉首尾静音。"""
    if x.size == 0:
        return x
    peak = float(np.max(np.abs(x)))
    if peak <= 0:
        return x
    idx = np.flatnonzero(np.abs(x) > peak * (10 ** (thr_db / 20.0)))
    if idx.size == 0:
        return x
    a = max(0, idx[0] - int(margin * sr))
    b = min(x.size, idx[-1] + 1 + int(margin * sr))
    return x[a:b]


def normalize_peak(x, target_dbfs=TARGET_DBFS):
    """峰值归一到 target_dbfs；全静音输入原样返回。"""
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 0:
        return x
    return x * (10 ** (target_dbfs / 20.0) / peak)


def fade(x, sr, ms=FADE_MS):
    """首尾短淡入淡出，避免切点爆音。"""
    n = int(sr * ms / 1000.0)
    if n < 2 or x.size <= 2 * n:
        return x
    ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)
    x = x.copy()
    x[:n] *= ramp
    x[-n:] *= ramp[::-1]
    return x


def postprocess(audio, sr, do_trim=True, target_dbfs=TARGET_DBFS, fade_ms=FADE_MS):
    """合成波形 → 可直接播放的波形（掐静音 + 峰值归一 + 淡入淡出）。"""
    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    if do_trim:
        x = trim_silence(x, sr)
    x = normalize_peak(x, target_dbfs)
    x = fade(x, sr, fade_ms)
    return x


def synthesize(text, onnx_path=DEFAULT_ONNX, voice_path=DEFAULT_VOICE,
               length_scale=None, noise_scale=None, noise_w=None,
               do_postprocess=True, target_dbfs=TARGET_DBFS):
    """Ye 拼音 → (float 波形, 采样率, 未识别音节数, id 数)。"""
    with open(voice_path, encoding="utf-8") as f:
        cfg = json.load(f)
    id_map = cfg["phoneme_id_map"]
    sr = int(cfg["audio"]["sample_rate"])
    infer = cfg.get("inference") or {}

    tokens, n_bad = tokenize_ye(text)
    # 音素表里没有的符号（旧版本音素表差异、拼写里的怪字符）直接丢弃并计数，
    # 否则 to_ids 会 KeyError 把整条合成打断。
    kept = [t for t in tokens if t in id_map]
    n_bad += len(tokens) - len(kept)
    # 汉字会被文本归一扫掉（不是 Ye 拼写），单独计数，避免「unknown: 0」的误导
    n_bad += len(_CJK_RE.findall(str(text)))
    if not [t for t in kept if t != " "]:
        raise ValueError("没有可用音素：输入必须是 Ye 拼音（如 af gov diex caf），"
                         "汉字/数字/标点会被忽略")
    ids = to_ids(kept, id_map)

    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    x = np.asarray([ids], dtype=np.int64)
    x_len = np.asarray([len(ids)], dtype=np.int64)
    scales = np.asarray([
        float(infer.get("noise_scale", 0.667) if noise_scale is None else noise_scale),
        float(infer.get("length_scale", 1.0) if length_scale is None else length_scale),
        float(infer.get("noise_w", 0.8) if noise_w is None else noise_w),
    ], dtype=np.float32)
    audio = sess.run(None, {"input": x, "input_lengths": x_len, "scales": scales})[0]
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if do_postprocess:
        audio = postprocess(audio, sr, target_dbfs=target_dbfs)
    return audio, sr, n_bad, len(ids)


def write_wav(path, audio, sr):
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description="土家语 VITS（v0.2）Ye 拼音 → 语音")
    ap.add_argument("--text", required=True, help='Ye 拼音，如 "hufnix davhar niev caif kax"')
    ap.add_argument("-o", "--out", default="out.wav", help="输出 wav 路径")
    ap.add_argument("--onnx", default=DEFAULT_ONNX, help="模型 .onnx")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="模型旁的 .onnx.json")
    ap.add_argument("--length-scale", type=float, default=None, help="语速：>1 更慢")
    ap.add_argument("--noise-scale", type=float, default=None)
    ap.add_argument("--noise-w", type=float, default=None)
    ap.add_argument("--no-trim", action="store_true", help="不掐首尾静音")
    ap.add_argument("--target-dbfs", type=float, default=TARGET_DBFS,
                    help="峰值归一目标（默认 -1 dBFS）")
    a = ap.parse_args()

    audio, sr, n_bad, n_ids = synthesize(
        a.text, a.onnx, a.voice, a.length_scale, a.noise_scale, a.noise_w,
        do_postprocess=not a.no_trim, target_dbfs=a.target_dbfs)
    write_wav(a.out, audio, sr)
    peak = 20 * np.log10(max(1e-9, float(np.max(np.abs(audio)))))
    print("text   :", a.text)
    print("ids    :", n_ids)
    print("unknown:", n_bad, "（>0 表示有音节/符号没有进入音素表）")
    print("audio  : %.2fs @ %d Hz, peak %.1f dBFS -> %s"
          % (len(audio) / sr, sr, peak, a.out))


if __name__ == "__main__":
    main()
