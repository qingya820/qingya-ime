#!/usr/bin/env python3
# 把 pwxcoo/chinese-xinhua (MIT) 的 xiehouyu.json 转成拼音词库 TSV：词\t拼音(空格分隔音节)\t词频
#
# 取数：
#   curl -L -o data/raw/xiehouyu.json \
#     https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/xiehouyu.json
# 打包（仓库根目录）：
#   cargo run --release -q -p qingjian-dict-convert -- --out-dir build \
#     pack dict --input build/xiehouyu.tsv --name "歇后语大全" --license MIT \
#     --attribution "pwxcoo/chinese-xinhua（MIT）" \
#     --source https://github.com/pwxcoo/chinese-xinhua
# 安装：把 build/xiehouyu.qj 放进用户词库目录
#   macOS: ~/Library/Application Support/Qingjian/dicts/
#   Windows: %APPDATA%\Qingjian\dicts\
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEX = ROOT / "assets/lexicon/dict.tsv"
SRC = ROOT / "data/raw/xiehouyu.json"
OUT = ROOT / "build/xiehouyu.tsv"

CJK = re.compile(r'[一-鿿]')
def is_cjk(ch):
    return bool(CJK.match(ch))

# 1) 单字 -> 最高词频读音；多字词 -> 整词音节（前向最大匹配，缓解多音字）
char_py = {}
phrase_py = {}
with open(LEX, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        word, py, freq = parts[0], parts[1], parts[2]
        if not all(is_cjk(c) for c in word):
            continue
        try:
            freq = int(freq)
        except ValueError:
            freq = 0
        if len(word) == 1:
            if word not in char_py or freq > char_py[word][1]:
                char_py[word] = (py, freq)
        else:
            syls = py.split()
            if len(syls) == len(word):
                old = phrase_py.get(word)
                if old is None or freq > old[1]:
                    phrase_py[word] = (syls, freq)

def annotate(han):
    """对纯汉字序列前向最大匹配多字词，回退单字音。返回音节 list 或 None。"""
    out = []
    i, n = 0, len(han)
    while i < n:
        matched = None
        for L in range(min(4, n - i), 1, -1):
            seg = "".join(han[i:i + L])
            hit = phrase_py.get(seg)
            if hit and len(hit[0]) == L:   # 音节数与字数一致才采用
                matched = hit[0]
                i += L
                break
        if matched is None:
            c = han[i]
            if c not in char_py:
                return None
            matched = [char_py[c][0]]
            i += 1
        out.extend(matched)
    return out

data = json.load(open(SRC, encoding="utf-8"))
seen = set()
rows = []
dropped = {"ascii": 0, "oov": 0, "len": 0, "dup": 0}
for item in data:
    riddle = (item.get("riddle") or "").strip()
    answer = (item.get("answer") or "").strip()
    if not riddle or not answer:
        continue
    answer = re.split(r'[；;]', answer)[0].strip()   # 多谜底取首选
    text = f"{riddle}——{answer}"
    han = [c for c in text if is_cjk(c)]
    if len(han) < 4 or len(han) > 16:
        dropped["len"] += 1
        continue
    if re.search(r'[A-Za-z0-9]', text):
        dropped["ascii"] += 1
        continue
    pys = annotate(han)
    if pys is None:
        dropped["oov"] += 1
        continue
    key = "".join(han)
    if key in seen:
        dropped["dup"] += 1
        continue
    seen.add(key)
    rows.append((text, " ".join(pys)))

OUT.parent.mkdir(parents=True, exist_ok=True)
rows.sort(key=lambda r: r[0])
with open(OUT, "w", encoding="utf-8") as f:
    for text, py in rows:
        f.write(f"{text}\t{py}\t100\n")

print(f"写出 {len(rows)} 条 -> {OUT}", file=sys.stderr)
print("丢弃:", dropped, file=sys.stderr)
