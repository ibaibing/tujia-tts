# -*- coding: utf-8 -*-
"""Ye 拼音 → 音素 id（本 release 自带，纯标准库）。

抽取自下列两处的 Ye 拼写解析部分，原样搬运，只为让本 release 脱离语料仓与训练代码即可运行：
  tujia-tts-lab/scripts/vits/build_vits_data.py         （tokenize_ye / syllable_tokens / to_ids）
  tujia-multimodal-corpus/scripts/zipa_forced_align.py  （Ye 音系表 + 音节切分 + 语料记法归一）

注意：这是**冻结副本**。声母/韵母表与音节规则的正源是 tujia_nlp.corpus；release 不引包，
改动正源后需同步这里的表（音素 id 由本文件的表决定，与已训练的 checkpoint 绑定）。
"""
import re

PAD, BOS, EOS, SPACE = "_", "^", "$", " "
TONE_TO_DIGIT = {"x": "1", "f": "2", "r": "3", "v": "4", "": "0"}

# ---- Ye 声母 → IPA（长匹配优先）----
YE_INITIAL_TO_IPA = {
    "b": "p", "p": "pʰ", "m": "m",
    "d": "t", "t": "tʰ", "n": "n", "l": "l",
    "g": "k", "k": "kʰ", "h": "x",
    "j": "tɕ", "q": "tɕʰ", "x": "ɕ",
    "z": "ts", "c": "tsʰ", "s": "s",
    "r": "z", "y": "j", "w": "w",
    "ny": "ɲ", "ng": "ŋ", "sh": "ʂ",
    "hh": "ɣ", "ch": "tʂʰ", "zh": "ʈʂ",
}
_YE_INITIALS = sorted(YE_INITIAL_TO_IPA, key=len, reverse=True)

# ---- Ye 韵母 → IPA（长匹配优先；鼻化韵按 base+n）----
YE_FINAL_TO_IPA = {
    "ii": "ɿ", "i": "i", "u": "u", "a": "a", "o": "o", "e": "ɤ", "ü": "y", "v": "y",
    "ai": "ai", "ei": "ei", "au": "au", "ou": "ou",
    "ia": "ia", "ie": "iɛ", "io": "io", "iau": "iau", "iou": "iou",
    "ua": "ua", "uai": "uai", "uei": "uei", "ui": "uei", "uo": "uo",
    "an": "ã", "en": "ẽ", "in": "ĩ", "on": "õ", "un": "ũ",
    "ian": "iã", "uan": "uã", "iun": "iũ", "uen": "uẽ",
    "ang": "aŋ", "eng": "eŋ", "ing": "iŋ", "ong": "oŋ", "iong": "ioŋ",
    "er": "ə",
}

TONE_LETTERS = set("xfrv")          # 55→x 35→f 21→r 53→v
WORD_SEP = set(" \t-~,;、|")

# 语料原样记法（星号借词 / 数字调 / 说话人标签）→ Ye 的归一用
_TONE_DIGIT = {"1": "x", "2": "f", "3": "r", "4": "v"}
_LOAN_RE = re.compile(r"\*([A-Za-z]+)\*([1-4]?)")
_SPEAKER_TAG_RE = re.compile(r"(?:^|\s)[A-Za-z\u4e00-\u9fff]{1,12}\s*[:：]")


def normalize_notation(text: str) -> str:
    """语料原样记法统一成叶德书 Ye 拼写（调号字母 x/f/r/v）。"""
    t = str(text)
    t = _LOAN_RE.sub(lambda m: " " + m.group(1) + (m.group(2) or "") + " ", t)
    t = t.replace("*", " ")
    t = _SPEAKER_TAG_RE.sub(" ", t)
    # 音节末 y 实为声调 v（53 高降）：语料里 y / v 混写
    t = re.sub(r"(?<=[aeiou])y(?![aeiou])", "v", t)
    t = re.sub(r"([1-4])(?=[A-Za-z])", r"\1 ", t)               # bi2zi1ka3 → bi2 zi1 ka3
    t = re.sub(r"(?<=[A-Za-z])[1-4](?![A-Za-z])",               # bi2 → bif
               lambda m: _TONE_DIGIT[m.group(0)], t)
    t = t.lower()
    t = re.sub(r"[^a-z\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _split_ye_syllables(chunk: str):
    """一串 Ye 字母切成音节（DP + 最长优先，切不动则整体作单音节）。"""
    n = len(chunk)
    memo = {}

    def valid_syllable(s: str):
        """返回 (声母, 韵母, 调) 或 None。"""
        if not s:
            return None
        tone, body = "", s
        if len(s) >= 2 and s[-1] in TONE_LETTERS:
            tone, body = s[-1], s[:-1]
        for ini in [""] + _YE_INITIALS:
            if ini and not body.startswith(ini):
                continue
            rest = body[len(ini):]
            if rest in YE_FINAL_TO_IPA:
                return ini, rest, tone
        return None

    def solve(i):
        if i == n:
            return []
        if i in memo:
            return memo[i]
        best = None
        for j in range(min(n, i + 6), i, -1):
            syl = chunk[i:j]
            if valid_syllable(syl):
                tail = solve(j)
                if tail is not None:
                    cand = [(syl, valid_syllable(syl))] + tail
                    if best is None or len(cand) < len(best):
                        best = cand
        memo[i] = best
        return best

    got = solve(0)
    if got is None:
        return [(chunk, None)]      # 切不动 → 原样当单音节，标低置信
    return got


def syllable_tokens(par):
    """(声母, 韵母, 调) → [IPA 音素..., 调 token]。

    1984 方案 p0008：韵母 i 接 z/c/s/r 时读 [ɿ]。课本写单 i，故此处按声母补规则；
    "ii" 映射保留，兼容旧数据。
    """
    ini, fin, tone = par
    if fin == "i" and ini in {"z", "c", "s", "r"}:
        fin_ipa = "ɿ"
    else:
        fin_ipa = YE_FINAL_TO_IPA.get(fin, "")
    ipa = YE_INITIAL_TO_IPA.get(ini, "") + fin_ipa
    return list(ipa) + ["T" + TONE_TO_DIGIT.get(tone, "0")]


def tokenize_ye(text):
    """Ye 拼写串 → token 序列（音素单字符 + 每音节一个调 token + 词界空格）。"""
    text = normalize_notation(text)
    toks, n_bad = [], 0
    for word in text.split():
        for _syl_text, par in _split_ye_syllables(word):
            if par is None:
                n_bad += 1
                continue
            toks += syllable_tokens(par)
        toks.append(SPACE)
    if toks and toks[-1] == SPACE:
        toks.pop()
    return toks, n_bad


def to_ids(tokens, id_map):
    """token 序列 → 模型 id 序列（BOS + 交错 PAD … + EOS）。"""
    ids = list(id_map[BOS]) + list(id_map[PAD])
    for t in tokens:
        ids += list(id_map[t]) + list(id_map[PAD])
    ids += list(id_map[EOS])
    return ids
