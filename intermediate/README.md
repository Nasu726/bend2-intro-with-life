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

[**完成までの執筆・実装予定**](COMPLETION_PLAN.md) に工程・ゲート・暫定スケジュールをまとめました。

## 制作の進捗と方針

[制作ロードマップ](ROADMAP.md)に計画書から引き継いだ内容と完成条件をまとめています。
[法則から実装へ進む教材草稿](minesweeper/LESSON.md)に加え、
[ListとArrayの章別補稿](manuscript/03_ListとArrayを選ぶ.md)と
[IO・Result・Fileの章別補稿](manuscript/06_IOと失敗を読む.md)を書き進めています。
[執筆進捗と優先順位](manuscript/STATUS.md)で本文と実行サンプルの対応を管理します。
2026-10-16の本文改稿で、第3・6・13・15・17・21章の説明を増補し、
**同じTeXからPDFと学習用ZIPを再生成済み**です。
引き続き第19・20・21章を増補し、さらに第11・12章を『はじめてのBend2』と同じ
**小さなコード→実行結果→仕組みの解説→演習**の流れに沿って改稿しました。
新たに `31_image_quadrants.bend`、`32_mouse_events.bend`、
`33_nat_induction.bend` と `34_mine_mask_law.bend` を追加し、学習用コードは**43ファイル**になりました。
第13〜18章は、マスの状態→座標の境界→旗操作の `law`→自然数の帰納法→
盤面全体の不変条件→検証範囲の順に書き直し、本文の重複も整理しました。
章別補稿とマインスイーパー草稿の全文が統合済みという意味ではなく、
残る内容は校正しながら順次取り込みます。

## マインスイーパーの法則駆動開発（制作途中）

ゲームの実装は[要件台帳](minesweeper/REQUIREMENTS.md)と
[LAWS.bend](minesweeper/LAWS.bend)を先に確定し、その後で
[実装](minesweeper/game.bend)と[証明](minesweeper/PROOF.bend)を作る方式です。

```sh
bend intermediate/minesweeper/PROOF.bend --verdict
```

現在は合計43法則を形式的に検査しています。16マスのArray状態と地雷マスク、
盤面全体のマスク不変性、隣接数、添字境界に加えて、
[純粋なクリック・勝敗ロジック](minesweeper/session.bend)も実装しました。
ゲームの遷移について独立した86件の実行テストを追加しています。
初手安全は `start.bend`、0領域の連鎖公開は `flood.bend` へ純粋関数として実装しました。
一般の隣接数の全称証明とCLI/GUI・保存の統合は未完成です。

## 公式資料とライセンス

- [Bend 2公式リポジトリ](https://github.com/bendlang/bend)
- [Bend 2公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [Bend 2公式リリース](https://github.com/bendlang/bend/releases)

本書と付属サンプルコードは[MIT License](../LICENSE)で公開しています。

今回の改稿では第5〜10章にも、`Maybe`・`Result`・`Either`、Fileの読み戻し、
IOの外部入力、Chanの受け渡し、TCP接続の成否を示す小さなコードと演習を補いました。
第6章に重複していた説明は整理し、各APIの詳しい説明は対応する章に置いています。
演習解説は [solutions/05_10_io_exercises.md](solutions/05_10_io_exercises.md) に分離しています。

第1・2・4・23章の再編集では、入門書の編集方針に沿って、
**必要性→実行可能な短い例→結果と型→解説→演習**の流れを強化しました。
`35_string_fields.bend`（文字列分割）、`36_map_missing.bend`（Mapにキーがあるか）、
`37_u32_dimension.bend`（Nat/U32変換と比較）を追加し、教材コードは**43ファイル**です（うち1ファイルはimport用モジュール）。

今回の第3章改稿では `38_list_sort.bend`、`39_array_to_list.bend`、`40_list_map.bend` を追加し、
標準の `List.sort`・`List.map`・`List.foldl`・`Array.to_list` を自分で動かして比較できます。
第19章にはCPUスレッド数を変えるコマンド、第20章には `board_index.bend` と
`42_module_board.bend` を使う二ファイルのimport実習を追加しました。
後者の `board_index.bend` はライブラリ用なので、`main` を持つ `42_module_board.bend` を実行します。

第20章には `43_target_hello.bend` を追加し、Bendの通常実行だけでなく
**ネイティブCへコンパイルして実行、生成JSをNode.jsで実行**する手順を載せています。
CIで三つとも42を出力することを照合しました。C生成には対応する `clang`、
JavaScript実行にはNode.jsが別途必要です。

第21章では0マスの連鎖公開を具体盤面から学べるよう追記し、
仕様を先行して固定した6法則、`List`による作業リスト、`Nat`による停止性検査も説明しています。
