# -*- coding: utf-8 -*-
"""Tujia VITS (v0.5) synthesis: Ye pinyin / IPA -> 16 kHz speech.

Usage:
  python3 synth.py --text "hufnix davhar niev caif kax" -o out.wav
  python3 synth.py --text "xu21 ni21" -o out.wav --notation ipa
  python3 synth.py --text "af gov diex caf" -o a.wav --length-scale 1.0

Input may be **Ye pinyin** (e.g. af gov diex caf) or **toned IPA** (e.g. a35 ko53);
the notation is detected automatically. Chinese characters are not supported.
Dependencies: onnxruntime, numpy, tujia-nlp. The model and its phoneme table
ship with this directory.

Pre-processing: notation cleanup (syllable-final y -> v) -> syllable split
-> initial/final to IPA -> one tone token per syllable -> unknown symbols are
dropped and counted instead of raising mid-synthesis.
Post-processing: trim leading/trailing silence -> peak normalise (default
-1 dBFS) -> 10 ms fade in/out.
"""
import argparse
import json
import os
import re
import wave

import numpy as np
import onnxruntime as ort

try:                       # imported as part of the tujia_tts package
    from .frontend import to_ids, tokenize
except ImportError:        # run directly: python3 synth.py
    from frontend import to_ids, tokenize

_CJK_RE = re.compile(r"[\u3400-\u9fff]")

HERE = os.path.dirname(os.path.abspath(__file__))
# When used directly the model sits next to the code; once installed it lives
# under tujia_tts/data/.
_DATA = os.path.join(HERE, "data")
if os.path.exists(os.path.join(_DATA, "vits_tujia-v0.5.onnx")):
    HERE = _DATA
DEFAULT_ONNX = os.path.join(HERE, "vits_tujia-v0.5.onnx")
DEFAULT_VOICE = os.path.join(HERE, "vits_tujia-v0.5.onnx.json")

TRIM_THR_DB = -40.0     # silence threshold relative to peak
TRIM_MARGIN = 0.03      # seconds kept around the trimmed region
TARGET_DBFS = -1.0      # peak normalisation target
FADE_MS = 10.0          # fade in/out length


def trim_silence(x, sr, thr_db=TRIM_THR_DB, margin=TRIM_MARGIN):
    """Trim leading/trailing silence using a threshold relative to the peak."""
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
    """Normalise the peak to target_dbfs; all-silent input is returned as is."""
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 0:
        return x
    return x * (10 ** (target_dbfs / 20.0) / peak)


def fade(x, sr, ms=FADE_MS):
    """Short fade in/out to avoid clicks at the cut points."""
    n = int(sr * ms / 1000.0)
    if n < 2 or x.size <= 2 * n:
        return x
    ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)
    x = x.copy()
    x[:n] *= ramp
    x[-n:] *= ramp[::-1]
    return x


def postprocess(audio, sr, do_trim=True, target_dbfs=TARGET_DBFS, fade_ms=FADE_MS):
    """Synthesized waveform -> playable waveform (trim + peak normalise + fade)."""
    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    if do_trim:
        x = trim_silence(x, sr)
    x = normalize_peak(x, target_dbfs)
    x = fade(x, sr, fade_ms)
    return x


def synthesize(text, onnx_path=DEFAULT_ONNX, voice_path=DEFAULT_VOICE,
               length_scale=None, noise_scale=None, noise_w=None,
               do_postprocess=True, target_dbfs=TARGET_DBFS, notation="auto"):
    """Ye pinyin or toned IPA -> (float waveform, sample rate, n_unknown, n_ids).

    ``notation``: ``"ye"`` / ``"ipa"`` / ``"auto"`` (default: detect by character).
    """
    with open(voice_path, encoding="utf-8") as f:
        cfg = json.load(f)
    id_map = cfg["phoneme_id_map"]
    sr = int(cfg["audio"]["sample_rate"])
    infer = cfg.get("inference") or {}

    tokens, n_bad = tokenize(text, notation=notation, id_map=id_map)
    # Symbols missing from the phoneme table (older inventories, stray
    # characters) are dropped and counted; otherwise to_ids would raise KeyError
    # and abort the whole synthesis.
    kept = [t for t in tokens if t in id_map]
    n_bad += len(tokens) - len(kept)
    # Chinese characters are stripped by the text cleanup (they are not Ye
    # spelling); count them so "unknown: 0" cannot mislead.
    n_bad += len(_CJK_RE.findall(str(text)))
    if not [t for t in kept if t != " "]:
        raise ValueError("no usable phonemes: input must be Ye pinyin "
                         "(e.g. af gov diex caf) or toned IPA (e.g. a35 ko53); "
                         "Chinese characters, digits and punctuation are ignored")
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
    ap = argparse.ArgumentParser(description="Tujia VITS (v0.5): Ye pinyin / IPA -> speech")
    ap.add_argument("--text", required=True,
                    help='Ye pinyin "hufnix davhar niev caif kax" or toned IPA "xu21 ni21"')
    ap.add_argument("--notation", choices=["auto", "ye", "ipa"], default="auto",
                    help="input notation (default: detect automatically)")
    ap.add_argument("-o", "--out", default="out.wav", help="output wav path")
    ap.add_argument("--onnx", default=DEFAULT_ONNX, help="model .onnx")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help=".onnx.json next to the model")
    ap.add_argument("--length-scale", type=float, default=None,
                    help="speaking rate: >1 is slower")
    ap.add_argument("--noise-scale", type=float, default=None)
    ap.add_argument("--noise-w", type=float, default=None)
    ap.add_argument("--no-trim", action="store_true",
                    help="keep leading/trailing silence")
    ap.add_argument("--target-dbfs", type=float, default=TARGET_DBFS,
                    help="peak normalisation target (default -1 dBFS)")
    a = ap.parse_args()

    audio, sr, n_bad, n_ids = synthesize(
        a.text, a.onnx, a.voice, a.length_scale, a.noise_scale, a.noise_w,
        do_postprocess=not a.no_trim, target_dbfs=a.target_dbfs, notation=a.notation)
    write_wav(a.out, audio, sr)
    peak = 20 * np.log10(max(1e-9, float(np.max(np.abs(audio)))))
    print("text   :", a.text)
    print("ids    :", n_ids)
    print("unknown:", n_bad, "(>0 means some syllables/symbols are not in the phoneme table)")
    print("audio  : %.2fs @ %d Hz, peak %.1f dBFS -> %s"
          % (len(audio) / sr, sr, peak, a.out))


if __name__ == "__main__":
    main()
