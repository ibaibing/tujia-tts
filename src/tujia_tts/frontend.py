# -*- coding: utf-8 -*-
"""Text front-end: Ye pinyin / IPA -> model phoneme tokens.

Syllable splitting, initial/final parsing and tone-notation normalisation are
delegated to **tujia-nlp** (``tujia_nlp.corpus`` / ``tujia_nlp.tones``); this
module does not carry a second parser. It only keeps what is bound to the
checkpoint: the 40-symbol inventory of v0.5 and the rule that appends one
``T0``-``T4`` tone token per syllable (unmarked syllables are read as 21 = ``T3``).

Accepted input:

* Ye pinyin ``hufnix davhar niev caif kax`` (tone letters x/f/r/v, or digits 1-4)
* IPA ``xu²¹ ni²¹`` / ``xu21 ni21`` / ``xu˨˩ ni˨˩`` (tone optional, defaults to 21 = T3)

``tokenize()`` detects the notation automatically; pass ``notation="ye"`` or
``notation="ipa"`` to force one parser.
"""
from __future__ import annotations

import re

from tujia_nlp.corpus import (
    FINAL_TO_IPA,
    INITIAL_TO_IPA,
    to_ipa as _ye_to_ipa_records,
)
from tujia_nlp.syllable import clean_ipa
from tujia_nlp.tones import from_superscript

PAD, BOS, EOS, SPACE = "_", "^", "$", " "

# Initial/final tables come straight from tujia-nlp, the same tables used for
# training: an/ang -> ã, en/eng -> ẽ, in/ing -> ĩ, on/ong -> ũ. The absence of
# õ and of aŋ in the v0.5 inventory follows directly from those tables; v0.5
# also drops the retroflex stop ʈ that v0.4 carried (unknown symbols are skipped
# and counted, so old spellings do not raise).
# Tone: Ye tone letter / Chao digits -> tone token. Unmarked syllables default to
# T3 (21): Tujia has no independent neutral tone, and the v0.4 model was trained
# with 21 as the unmarked reading.
TONE_TO_TOKEN = {
    "x": "T1", "1": "T1", "55": "T1",
    "f": "T2", "2": "T2", "35": "T2",
    "r": "T3", "3": "T3", "21": "T3",
    "v": "T4", "4": "T4", "53": "T4",
    "": "T3",
}

CHAO_LETTERS = {"˥": "5", "˦": "4", "˧": "3", "˨": "2", "˩": "1"}

IPA_ONLY = set("ɕɣɿʈʂʰɛɤɲŋãẽĩũõəɨʧʤʦʣɔɪʊʏɯ")


def detect_notation(text: str) -> str:
    """Guess whether the input is IPA or Ye pinyin."""
    t = str(text)
    if any(ch in IPA_ONLY for ch in t):
        return "ipa"
    if re.search(r"[0-9⁰¹²³⁴⁵⁶⁷⁸⁹˥˦˧˨˩]", t):
        return "ipa"
    return "ye"


def _looks_ipa(text: str) -> bool:
    """Whether the input carries an IPA-specific hint (symbol, tone digit, Chao mark).

    Guards against forcing misspelled Ye input (``zzz qqq``) through the IPA parser.
    """
    t = str(text)
    return any(ch in IPA_ONLY for ch in t) or bool(
        re.search(r"[0-9⁰¹²³⁴⁵⁶⁷⁸⁹˥˦˧˨˩]", t))


def _normalize_corpus_text(text: str) -> str:
    """Minimal inference-side normalisation: only forms the parser rejects.

    Digit tones (``bi2zi1ka3``) are handled natively by
    ``tujia_nlp.corpus.parse_syllable`` and are not rewritten here. Only the
    syllable-final ``y`` (corpora mix ``y`` and ``v``; ``y`` means tone 53) is
    folded to ``v`` and punctuation is stripped.

    Training-side corpus cleanup (parenthetical variants, ``~`` repetition,
    ``hx`` -> ``hh``, tolerant splitting) describes corpus noise and stays in
    the training repository; it is not part of the release package.
    """
    t = str(text).lower()
    t = re.sub(r"(?<=[aeiou])y(?![aeiou])", "v", t)
    t = re.sub(r"(?<=[nmg])y(?![aeiou])", "v", t)
    t = re.sub(r"[^a-z0-9ü\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tokenize_ye(text: str):
    """Ye pinyin -> (token list, number of unrecognised syllables).

    Splitting and the initial/final tables come from tujia-nlp; this function
    only applies ``z/c/s/r + i -> ɿ`` and appends one tone token per syllable
    (unmarked -> T3).
    """
    toks, n_bad = [], 0
    for word in _normalize_corpus_text(text).split():
        for rec in _ye_to_ipa_records(word):
            if not rec["ok"]:
                n_bad += 1
                continue
            ini, fin, tone = rec["initial"], rec["final"], rec["tone"]
            if fin == "i" and ini in {"z", "c", "s", "r"}:
                fin_ipa = "ɿ"           # 1984 scheme: z/c/s/r + i is read [ɿ]
            else:
                fin_ipa = FINAL_TO_IPA.get(fin)
            if fin_ipa is None:
                n_bad += 1
                continue
            toks += list(INITIAL_TO_IPA.get(ini, "") + fin_ipa)
            toks.append(TONE_TO_TOKEN.get(tone, "T3"))
        toks.append(SPACE)
    if toks and toks[-1] == SPACE:
        toks.pop()
    return toks, n_bad


def tokenize_ipa(text: str, id_map=None):
    """Toned IPA -> (token list, number of unrecognised symbols).

    Tones may be written as superscripts (``xu²¹``), Chao letters (``xu˨˩``)
    or ASCII digits (``xu21``); omitted tones become T3 (21). Syllables are cut at
    tone marks and symbols are split per character, matching training.
    """
    toks, n_bad = [], 0
    for word in str(text).split():
        w = word.translate(str.maketrans(CHAO_LETTERS))
        m = re.search(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+$", w)
        if m:                                # superscript tone -> ASCII via tujia-nlp
            w = w[:m.start()] + from_superscript(m.group(0))
        w = clean_ipa(w)
        cur, tone = "", ""
        pieces = []
        for ch in w:
            if ch.isdigit():
                tone += ch
            else:
                if tone and cur:
                    pieces.append((cur, tone))
                    cur, tone = "", ""
                cur += ch
        if cur:
            pieces.append((cur, tone))
        if not pieces:
            n_bad += 1
            continue
        for body, t in pieces:
            for ch in body:
                if id_map is not None and ch not in id_map:
                    n_bad += 1
                else:
                    toks.append(ch)
            toks.append(TONE_TO_TOKEN.get(t, "T3"))
        toks.append(SPACE)
    if toks and toks[-1] == SPACE:
        toks.pop()
    return toks, n_bad


def tokenize(text: str, notation: str = "auto", id_map=None):
    """Single entry point: (token list, number of unrecognised items).

    ``auto`` decides by character first; if no syllable parses as Ye pinyin it
    falls back to the IPA parser, which covers inputs such as ``la35`` that
    carry a tone digit but no IPA-only symbol.
    """
    mode = detect_notation(text) if notation == "auto" else notation
    if mode == "ipa":
        return tokenize_ipa(text, id_map=id_map)
    toks, n_bad = tokenize_ye(text)
    if n_bad and not [t for t in toks if t != SPACE] and _looks_ipa(text):
        alt, nb2 = tokenize_ipa(text, id_map=id_map)
        if [t for t in alt if t != SPACE]:
            return alt, nb2
    return toks, n_bad


def to_ids(tokens, id_map):
    """Token list -> model id sequence (BOS + interleaved PAD ... + EOS)."""
    ids = list(id_map[BOS]) + list(id_map[PAD])
    for t in tokens:
        ids += list(id_map[t]) + list(id_map[PAD])
    ids += list(id_map[EOS])
    return ids
