# Bend 2を使いこなす

**マインスイーパーを題材に、Bend 2を自分の道具として使えるようになるための日本語教材**です。入門書[『ライフゲームで学ぶ はじめてのBend2』](../README.md)の続編として、まず利用できる機能の全体像を掴み、実際にプログラムを書くとき困らないよう、関数の型、戻り値、所有権、失敗時の動作まで説明します。

書名の「使いこなす」は難しいハックを意味しません。必要な機能を探し、適切に選んで実装・検証できることを目指します。マインスイーパーは共通の実習題材です。ゲームでは使わない機能も、独立した例を通して学びます。

## 教材のダウンロード

**[教科書PDF＋実習用サンプルコードをまとめてダウンロード（ZIP）](../reader-packages/bend2-intermediate-reader-preview.zip)**

ZIPを展開すると、教科書PDF、実習用コード、使い始めるための案内が入っています。**リポジトリをクローンする必要はありません。**

[PDFだけを読む](Bend2を使いこなす_プレビュー.pdf)

## 学べること

- **データと型**：数値・文字列、`List`・`Array`・`Map`・`Set`、`Maybe`・`Result`、型と数量指定
- **入出力**：ファイルの保存と読み込み、乱数、環境変数、プロセス、通信
- **並行・並列処理**：`IO.fork`・`Chan`、CPU/GPUでの計算
- **GUI**：`Image`・`App`・イベントの扱い
- **形式的証明**：`law`で仕様を表す方法、等式、帰納法、不変条件
- **実践**：マインスイーパーの状態・操作・描画と、運ゲー無し版の考え方

本文は6 Partsに分かれています。最初から順番に進めても、必要な機能の章を参照しても構いません。

## コードを動かす

[Bend 2の公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)に従ってBendをインストールし、ZIPを展開したフォルダーで実行してください。

```sh
bend examples/01_set.bend
bend examples/02_map.bend
bend examples/04_flag_laws.bend --verdict
```

サンプルは**Bend 2.0.37**を基準に検証しています。`--verdict`による証明の確認にはLean 4も必要です。GUIの例はデスクトップ環境で動かしてください。

現在は**執筆途中のプレビュー版**で、教材全体はまだ未完成です。マインスイーパーの完成したGUIアプリや、運ゲー無し盤面のBendによる生成はまだ収録していません。演習の参考実装や追加の技術資料は、必要に応じて[リポジトリ内の参考コード](solutions/)から参照できます。

## 制作の進捗と方針

[制作ロードマップ](ROADMAP.md)に計画書から引き継いだ内容と完成条件をまとめています。
[法則から実装へ進む教材草稿](minesweeper/LESSON.md)も参照できます。
この草稿はまだPDFへ反映されていません。

## マインスイーパーの法則駆動開発（制作途中）

ゲームの実装は[要件台帳](minesweeper/REQUIREMENTS.md)と
[LAWS.bend](minesweeper/LAWS.bend)を先に確定し、その後で
[実装](minesweeper/game.bend)と[証明](minesweeper/PROOF.bend)を作る方式です。

```sh
bend intermediate/minesweeper/PROOF.bend --verdict
```

現在の証明範囲はマス単体の旗と公開操作だけです。盤面全体やGUIの
正当性はまだ証明・実装されていません。

## 公式資料とライセンス

- [Bend 2公式リポジトリ](https://github.com/bendlang/bend)
- [Bend 2公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [Bend 2公式リリース](https://github.com/bendlang/bend/releases)

本書と付属サンプルコードは[MIT License](../LICENSE)で公開しています。
