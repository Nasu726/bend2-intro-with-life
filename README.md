# ライフゲームで学ぶ はじめてのBend2

Bend 2 の基礎文法から、ライフゲームの実装、並列計算、依存型・形式的な証明までを、**実際にコードを書きながら**学ぶ日本語の入門教科書です。プログラミング経験が少ない方にも読めるよう、専門用語は登場箇所で簡潔に説明しています。

**執筆基準:** Bend 2.0.36 ／ **CI検証:** Bend 2.0.37 ／ **版:** 第1版（2026-10-16） ／ **形式:** XeLaTeX・PDF ／ **構成:** 全5 Part・37章

## 📖 教科書

- [**教科書PDF：ライフゲームで学ぶ はじめてのBend2**](ライフゲームで学ぶ_はじめてのBend2.pdf)
- [TeX原稿](Bend2_Life_Textbook.tex)
- [基本機能の監査・実装状況](FEATURE_AUDIT.md)

Part IはBend 2の言語機能を学び、ライフゲームのルールはPart IIの冒頭で導入します。各Partの冒頭では、**Part見出しと当該Partの章別目次を同じページ**に配置しています。本文は「です・ます」調を基本とし、重要な用語には太字と英語表記を付けています。冒頭には、データ型・関数・引数などの用語表も用意しました。

## 🎮 作るもの

8×8のトーラス型のライフゲーム（Conway's Game of Life）を、ターミナル上で5世代分表示するプログラムです。

1. **Part I — Bend 2の基礎:** ゲーム固有の設定に入る前に、データ型、関数、パターンマッチ、配列、アフィン性、リスト、高階関数、クロージャなど、言語の機能を学びます。
2. **Part II — ライフゲームの設計・実装:** まずゲームの規則と受け入れ条件を定め、初期配置、8近傍、同期更新、描画、Python参照実装を使ったテストまで進みます。
3. **Part III — アプリケーション:** モナドを詳しく学んでから、入出力、ファイル、並行処理、GUIに進みます。
4. **Part IV — 応用:** 再帰、所有権、CPU/GPU並列、性能測定、依存型、形式的証明を扱います。
5. **Part V — 補足:** 演習の解答、コマンド、機能監査をまとめています。

CPU/GPUでの並列ライフゲーム本体、GUI版、盤面全体の形式的証明は、**発展的な制作課題**です。完成済みであるとは記載していません。

## 🛠️ 動かす

公式インストールスクリプトは、実行前に内容を確認してください。Bend 2は初代Bendとは異なる言語です。

```sh
curl -fsSL https://bend-lang.com/install.sh -o install-bend.sh
# 事前に install-bend.sh の内容を確認してください。
sh install-bend.sh
export PATH="$HOME/.bend/bin:$PATH"
bend version
bend guide
```

付属コードを試す場合：

```sh
bend src/01_hello.bend
bend src/08_life_terminal.bend
python3 -m unittest discover -s tests -v
python3 scripts/check_bend.py
```

`src/12_affine_probe_INVALID.bend` は、**型エラーを観察するために意図的に誤ったコード**です。通常の確認対象から除外してください。`src/26_file_write.bend` はカレントディレクトリの `life-demo-output.txt` を上書きします。

## 🧪 テストとPDFの再生成

```sh
make test        # Python参照実装6件＋教科書構成3件（失敗時は非ゼロ終了）
make bend-check  # Bendを使った各サンプルの型チェック
make check       # Bend製ライフゲームとPython参照実装の出力比較
make pdf         # XeLaTeXで本文を3回組版
```

PDFを自分で組版するには、XeLaTeX、Notoの日本語フォントと、`xeCJK`、`etoc`、`tcolorbox`、`listings`、`tikz` などのLaTeXパッケージが必要です。生成途中のファイルは `build/` に入ります。

### GitHub Actionsでの検証

PR作成時とmainへのpush時に、Pythonの参照テストと教材構成の検査、Bendの型検査、ライフゲーム出力のオラクルとの完全一致検査を実行します。Bendの実行環境を作れない場合もスキップせず失敗させます。CIが成功してからマージしてください。

### 検証状況

- **以前のCIで確認済み（今回の追加サンプルもPRで再検証）:** Python参照テスト6件、Bend 2.0.37による全サンプルの型検査、意図的な所有権エラーの検出、生死規則18ケース、5世代分の全セル照合、および異常時の非ゼロ終了。
- **未確認:** GUI起動、GPU実行、`--verdict` による証明検査。
- **未実装:** ライフゲーム本体のGPU版・CPUタイル並列版、盤面全体の形式的な証明。

利用するBendのバージョンによって構文やAPIが変わる場合があります。まずインストールした環境の `bend guide` と `bend base` を参照してください。

## 📚 参考資料

- [Bend 公式リポジトリ](https://github.com/bendlang/bend)
- [Bend 公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [Bend 公式リリース](https://github.com/bendlang/bend/releases)

## ライセンス

本リポジトリに収録した教材および付属コードは、[MIT License](LICENSE) で公開する構成です。外部のBend言語処理系や参考資料のライセンスは、それぞれの原著作者の定めに従います。

## 配列の長さと多次元配列

64要素は本書の8×8盤面のサイズであり、言語の上限ではありません。`[0 : U32*256n]`で256要素を作れます。`Array.new(U32, 8n, 0)`は深さ8（2^8個）の配列です。`Array<Array<U32>>`で入れ子の配列も表現できますが、本書の完成版では座標計算を簡単にするため一次元配列を使用します。
