# マインスイーパーで学ぶ Bend 2 中級（制作中）

前巻[『ライフゲームで学ぶ はじめてのBend2』](../README.md)で説明しきれなかった**Bend 2の標準ライブラリ、データ構造、詳細な型・所有権の扱い、IO、GUI、形式的証明、並列実行、外部連携**を学ぶ日本語の続編です。

**主目的はBend 2の仕様を体系的に理解し、必要な機能を適切に使えるようになることです。** マインスイーパーは、そのための共通実習題材です。作品で使わないAPIも独立したコード例・解説で扱います。

## 教材

- [TeX原稿](Intermediate_Textbook.tex)
- **[教科書PDF（レビュー用初稿・36ページ）](マインスイーパーで学ぶ_Bend2中級_初稿.pdf)**
- [独立して動かせる教材コード](src/)
- [機能カバレッジと検証記録](COVERAGE.md)

現在は**レビュー用の初稿**です。章ごとに執筆・実装・型検査・実行検証・証明検査を進めます。フル機能の遊べるマインスイーパーおよび「運ゲー無し」生成は、この段階では未完成です。

## 読み進め方

1. Part Iで`Base`、`List`、`Array`、`Map`、`Set`等を学びます。
2. Part IIでファイル・引数・乱数・通信・並行IOを学びます。
3. Part IIIで`Image`・`App`によるGUIを学びます。
4. Part IVで`law`による仕様定義と形式的証明を実践します。
5. Part VでCPU/GPU・外部言語連携・パッケージを学びます。
6. Part VIでマインスイーパーに統合し、発展課題を扱います。

## 動作確認

公式の[インストール手順](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)に従いBend 2を導入してください。教材はBend 2.0.37を基準に検査します。

```sh
bend intermediate/src/01_set.bend
bend intermediate/src/02_map.bend
bend intermediate/src/04_flag_laws.bend --verdict
python3 -m unittest discover -s intermediate/tests -v
```

GUIサンプルは画面が開ける環境でのみ実行してください。CIでは原則として型検査し、GUI動作を検証済みとは主張しません。

## 正しさについて

型検査・実行テスト・形式的証明は別です。証明済みという表示は、`--verdict`が成功した命題に限定します。マインスイーパーの地雷配置、GUI、入出力処理までを一括して証明したわけではありません。

## 公式資料

- [Bend 2公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [標準ライブラリの実装（Base）](https://github.com/bendlang/bend/blob/main/bend2/base.bend)
- [Bendのリリース](https://github.com/bendlang/bend/releases)

前巻と同じく[MIT License](../LICENSE)を適用します。
