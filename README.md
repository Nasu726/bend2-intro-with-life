# ライフゲームで学ぶ はじめてのBend2

少しだけプログラミング経験のある人が、**Bend 2の基本文法をコードで確かめながら学び、ライフゲームを完成させる**ための日本語の教科書です。値とデータ型、関数、パターンマッチ、配列と所有権、リスト、高階関数、クロージャ、モナド、モジュールを扱います。

**刊行上の版:** 第1版 ／ **検証用コンパイラ:** Bend 2.0.37 ／ **形式:** XeLaTeX・PDF ／ **構成:** 3 Part・21章

## 教科書

- [教科書PDF](ライフゲームで学ぶ_はじめてのBend2.pdf)
- [LaTeX原稿](Bend2_Life_Textbook.tex)

**Part I**はBend 2の基本文法、**Part II**はライフゲームの仕様と実装、**Part III**は演習の解答とコマンド資料です。各Partの冒頭に、そのPartの章別目次を掲載しています。

## ハンズオン

8×8のトーラス型ライフゲーム（B3/S23）を5世代分表示するプログラムを、関数ごとに組み立てます。

```sh
bend src/01_hello.bend
bend src/08_life_terminal.bend
python3 -m unittest discover -s tests -v
python3 scripts/test_bend_runtime.py
```

Bend未導入の場合、Bendの実行テストはスキップされず、**非ゼロ終了**します。`src/12_affine_probe_INVALID.bend` は所有権エラーを観察するための意図的な失敗例です。

## インストール

公式インストールスクリプトは、内容を確認してから実行してください。

```sh
curl -fsSL https://bend-lang.com/install.sh -o install-bend.sh
# 内容を確認してから実行
sh install-bend.sh
export PATH="$HOME/.bend/bin:$PATH"
bend version
bend guide
```

## テストとPDFの再生成

```sh
make test         # Python参照テストと教材構成テスト
make bend-check   # Bendサンプルの型検査（意図的な失敗例を除く）
make bend-test    # Bend実行と期待値の照合
make pdf          # XeLaTeXを3回実行してPDFを更新
```

GitHub ActionsはPRとmainへのpushでPython・Bendのテストを実行し、エラーは正常終了として扱いません。PDFの再組版にはXeLaTeX、日本語Notoフォント、`xeCJK`、`etoc`、`tcolorbox`、`listings`、`tikz`等が必要です。

## テスト済みの項目

Bend 2.0.37による型検査と、ライフゲームの生死規則18ケース、5世代の盤面、モナドの`do`/`bind`の成功・失敗、高階関数の結果を検査するCIを用意しています。テストを実施したバージョンを変更した際は再確認してください。

## 配列の長さ

`Array`の長さは64固定ではありません。`[0 : U32*256n]`で256要素を作れます。また`Array<Array<U32>>`で入れ子の配列を表せます。完成作品では8×8の盤面に合わせ、一次元の64要素を使用します。

## ライセンス

本リポジトリの教材とサンプルコードは[MIT License](LICENSE)で公開する構成です。外部のBend処理系や参考資料の権利はそれぞれの提供元に帰属します。

## 参照

- [公式リポジトリ](https://github.com/bendlang/bend)
- [公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [公式リリース](https://github.com/bendlang/bend/releases)
