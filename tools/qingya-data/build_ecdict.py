#!/usr/bin/env python3
# 从 ECDICT（skywind3000/ECDICT，MIT）生成两份扩充数据：
#  1) build/english.tsv           英文补全词表  word \t code \t freq
#  2) build/glossary-extra-en.tsv 反转得到的中文→英文译词（仅补现有译词表没有的词，每词≤2译）
#
# 取数（ecdict.csv 约 77 万行 / 64MB，在 stardict.csv 或 release 的 ec.tar.zib 里）：
#   mkdir -p data/raw && curl -L -o data/raw/ecdict.csv \
#     https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv
#
# 合入现有译词表（assets/glossary/glossary-en.tsv）：
#   cat assets/glossary/glossary-en.tsv build/glossary-extra-en.tsv > build/glossary-en.tsv
# 再按 apps/macos/scripts/bundle.sh 的 pack glossary 流程重打；英文词表直接替换
# assets/lexicon/english.tsv 与 data/generated/english.tsv。
#
# 关键：ECDICT 的 bnc / frq 都是“排名”（1 最常用，数字越大越生僻），不是频次。
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data/raw/ecdict.csv"
EXIST_GLOSS = ROOT / "assets/glossary/glossary-en.tsv"
OUT_EN = ROOT / "build/english.tsv"
OUT_GLOSS = ROOT / "build/glossary-extra-en.tsv"

HAN = re.compile(r'^[一-鿿]+$')
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’\-]{0,31}$")
POS = {"n": "n.", "v": "v.", "adj": "adj.", "adv": "adv.", "pron": "pron.",
       "prep": "prep.", "conj": "conj.", "num": "num.", "int": "int.",
       "m": "m.", "phr": "phr."}
POS_RE = re.compile(r'^(n|v|adj|adv|pron|prep|conj|num|int|interj|m|phr|art|det|aux)\.\s*')
PAREN = re.compile(r'[（(][^（）()]*[)）]')

existing = set()
with open(EXIST_GLOSS, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        key = line.split("\t", 1)[0].strip()
        if key:
            existing.add(key)
print("现有译词表词条:", len(existing), file=sys.stderr)

best_word = {}      # code -> (score, original_word)
gloss = {}          # 中文词 -> set((score, pos, word))

# 词频量纲必须是 wordfreq 的 Zipf×1000（范围约 0–7800，见上游 english.tsv），
# 混输比分用 english_log_prob = (f/1000 − 9)·ln10。曾误用“2_000_000−排名”
# （最高近 200 万 = Zipf 2000），导致 chang/yong/dong 这类拼音同形英文词
# 在「拼音头+英文尾」路径碾压正常拼音，平常/使用/自动全打不出来。
#
# 排名→Zipf：Zipf 定律 P(r)=P₁/r，r=1（the）取 Zipf 7.6：
#   zipf(r) = 7.6 − log10(r)，下限 0（未登录词）。
ZIPF_R1 = 7.6
import math
def to_score(frq, bnc):
    frq = int(frq) if frq.isdigit() else 0
    bnc = int(bnc) if bnc.isdigit() else 0
    r = bnc or frq
    if not r:
        return 0                         # 无排名生僻词，不能给虚高频次
    z = ZIPF_R1 - math.log10(r)
    return max(0, round(z * 1000))

with open(CSV_PATH, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    n = 0
    for row in reader:
        n += 1
        word = (row.get("word") or "").strip()
        trans = (row.get("translation") or "").strip()
        score = to_score(row.get("frq", ""), row.get("bnc", ""))

        if WORD_RE.match(word):
            code = word.lower().replace("’", "'")
            if code not in best_word or score > best_word[code][0]:
                best_word[code] = (score, word)

        if not trans:
            continue
        for seg in trans.split("\\n"):
            seg = seg.strip()
            if not seg or seg.startswith("["):
                continue
            pos = None
            m = POS_RE.match(seg)
            if m:
                tag = "int" if m.group(1) == "interj" else m.group(1)
                pos = POS.get(tag)
                seg = seg[m.end():]
            seg = PAREN.sub("", seg)
            for chunk in re.split(r'[；;、，,]', seg):
                piece = chunk.strip(' 　,，、“”"\'…·.·:：')
                if 1 <= len(piece) <= 8 and HAN.match(piece):
                    gloss.setdefault(piece, set()).add((score, pos, word))

print("ECDICT 行:", n, file=sys.stderr)

OUT_EN.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_EN, "w", encoding="utf-8") as f:
    f.write("# 英文补全词表：来源 ECDICT（skywind3000，MIT）。词\t编码\t词频\n")
    for code, (score, word) in sorted(best_word.items(), key=lambda kv: -kv[1][0]):
        f.write(f"{word}\t{code}\t{score}\n")
print("英文词表词条:", len(best_word), file=sys.stderr)

added = 0
with open(OUT_GLOSS, "w", encoding="utf-8") as f:
    for key in sorted(gloss):
        if key in existing:
            continue
        cands = sorted(gloss[key], key=lambda x: -x[0])[:2]
        cols = []
        for score, pos, w in cands:
            w = w.replace("\t", " ").strip()
            if not w:
                continue
            cols.append(f"{pos} {w}" if pos else w)
        if cols:
            f.write(key + "\t" + "\t".join(cols) + "\n")
            added += 1
print("新增中文→英文词条:", added, file=sys.stderr)
