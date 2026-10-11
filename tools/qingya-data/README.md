# 青崖 fork 定制数据构建

个人 fork 在官方全量数据（`tools/release/data-fetch.sh` 拉 data-v5）之上的增量与构建脚本。
原始大数据文件不进仓库（`/data` 在 .gitignore），只放脚本，按本说明可复现。

## 1. logo

```sh
python3 tools/qingya-data/make_logo.py ~/Pictures/青崖logo.jpg
```

四角取底色补成 1024 见方 PNG 覆盖 `assets/icon/logo.png`，`bundle.sh` 再生成全套 icns。
菜单栏模板图是另一套：`assets/icon/make-menu-pdf.swift`（22pt 矢量 PDF，单色山字 40% 居中）。

## 2. 歇后语词库（pwxcoo/chinese-xinhua，MIT）

```sh
mkdir -p data/raw build
curl -L -o data/raw/xiehouyu.json \
  https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/xiehouyu.json
python3 tools/qingya-data/build_xiehouyu.py
cargo run --release -q -p qingjian-dict-convert -- --out-dir build \
  pack dict --input build/xiehouyu.tsv --name "歇后语大全" --license MIT \
  --attribution "pwxcoo/chinese-xinhua（MIT）" \
  --source https://github.com/pwxcoo/chinese-xinhua
```

拼音用 `assets/lexicon/dict.tsv` 做前向最大匹配标注（多字词优先，回退单字高频读音）。
成品 `build/xiehouyu.qj` 放用户词库目录即自动加载（升级不丢）：

- macOS：`~/Library/Application Support/Qingjian/dicts/`
- Windows：`%APPDATA%\Qingjian\dicts\`

## 3. 英文扩充（ECDICT，skywind3000/ECDICT，MIT）

```sh
curl -L -o data/raw/ecdict.csv \
  https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv
python3 tools/qingya-data/build_ecdict.py
cp build/english.tsv assets/lexicon/english.tsv
cp build/english.tsv data/generated/english.tsv
cat assets/glossary/glossary-en.tsv build/glossary-extra-en.tsv > /tmp/glossary-en.tsv
cp /tmp/glossary-en.tsv assets/glossary/glossary-en.tsv
```

下次 `bundle.sh` 检测到 TSV 比 .qj 新会自动重打 glossary-en.qj。
**注意 ECDICT 的 `bnc`/`frq` 是排名不是频次**（1 最常用），排序要反过来。

## 4. 打包 / 分发

- macOS：`apps/macos/scripts/bundle.sh --pkg`（本机架构；arm64 包即 M 系列 Mac 用）
- Windows：仓库 Actions 的 `fork-windows-build`（workflow_dispatch），
  拉官方数据后用仓库里扩充版 english.tsv / glossary-en 覆盖再出 Inno 安装包
- 新机安装后把 `xiehouyu.qj`、`qingya-custom.qj` 与全开 domains 的 `config.toml`
  放进对应用户数据目录（见桌面「青崖输入法分发」文件夹的一键脚本）
