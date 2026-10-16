# ライフゲームで学ぶ はじめてのBend2

**ライフゲームを作りながら、Bend 2の基本的な機能や書き方を学ぶための日本語の入門書**です。短いコードを読み、実際に動かしながら、データ型や関数などの基本文法から、Bend 2に特徴的な言語機能まで順に学びます。

基本的なプログラミング経験がある方を対象にしています。手続き型言語にしか触れたことがなくても読み進められるよう、新しい用語や記法を順に説明します。

## 教科書

- **[PDFを読む](ライフゲームで学ぶ_はじめてのBend2.pdf)**（第1版）
- [LaTeX原稿](Bend2_Life_Textbook.tex)

## 学べること

- **基本文法**：データ型、関数、パターンマッチ、配列、リスト、ユーザー定義型
- **Bend 2の特徴**：アフィン性と所有権、高階関数、クロージャ、モナド、テンプレート
- **プログラムの構成**：モジュール、入出力、再帰的な処理
- **並列計算と証明の入門**：CPU/GPU呼び出しの基本、`law`を使った形式的証明

本書は、基本文法を学ぶPart I、ライフゲームを使って実践するPart II、演習解答とコマンド資料を収録したPart IIIで構成されています。

## コードを動かす

[Bend 2の公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)に従ってBendをインストールしてから、リポジトリ内で次のコマンドを実行してください。

```sh
bend version
bend src/01_hello.bend
bend src/02_arithmetic.bend
bend src/08_life_terminal.bend
```

各章のサンプルコードは[`src/`](src/)にあります。コードを変更し、実行結果やエラーメッセージを確かめながら読み進めてください。

サンプルコードは**Bend 2.0.37**で動作確認しています。Bendのバージョンによって記法や動作が異なる場合があります。

## Bend 2の公式資料

- [公式リポジトリ](https://github.com/bendlang/bend)
- [公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [公式リリース](https://github.com/bendlang/bend/releases)

## ライセンス

本書と付属のサンプルコードは[MIT License](LICENSE)で公開しています。
