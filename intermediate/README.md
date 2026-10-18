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
bend examples/minesweeper/cli_replay.bend c0 f1 c1
bend examples/minesweeper/gui.bend -o minesweeper
./minesweeper
bend examples/minesweeper/public_solver.bend
bend examples/minesweeper/noguess_generator.bend
bend examples/minesweeper/cli_save.bend save c0 f1
bend examples/minesweeper/cli_save.bend load
```

サンプルは**Bend 2.0.37**を基準に検証しています。`--verdict`による証明の確認にはLean 4も必要です。GUIの例はデスクトップ環境で動かしてください。LinuxでのネイティブGUIビルドには `libx11-dev` が必要です。

第21章では、同梱の `examples/minesweeper/cli_replay.bend` と関連6モジュールで4×4ゲームの操作を再生できます。`c0` は番号0のクリック、`f1` は番号1の旗、`r` はリセットです。これは**引数を一括指定する実習**であり、まだ対話式CLIではありません。固定の地雷配置で初手安全・勝敗・0連鎖を学びます。

現在は**執筆途中のプレビュー版**です。マインスイーパーGUIの実装、Bend型検査、ネイティブコンパイル、座標・状態・未知のマウスボタンの13件の純粋テストは用意しました。画面上での実機操作確認とGUI本体の保存・復元、任意の大きさの運ゲー無し盤面生成はまだ完了していません。一方、固定4×4 CLIの操作履歴保存・復元と、4×4・地雷2個・左上開始に限定したBend製の運ゲー無し生成器は動作検証済みです。演習の参考実装や追加の技術資料は、必要に応じて[リポジトリ内の参考コード](solutions/)から参照できます。

[**完成までの執筆・実装予定**](COMPLETION_PLAN.md) に工程・ゲート・暫定スケジュールをまとめました。

## 第7・8章の実行確認（File・時刻）

第7章のバイナリ例は、文字列ではなく4バイトを保存して読み戻します。第8章の時計例は、待機前後の時刻から経過ミリ秒を求めます。どちらもZIP展開後の作業フォルダーで試せます。

```sh
bend examples/45_binary_file.bend
python3 -c "from pathlib import Path; print(Path('sample_bytes.bin').read_bytes().hex(' '))"
bend examples/46_elapsed_clock.bend
```

最初の出力は`4`、次は`00 0a 0d ff`、最後は経過時間を表す整数です。時計の値は環境によって変わり、常に`20`になるとは限りません。ファイルの個数だけでは内容の正しさを保証できないため、4バイトの値と順序を別に確かめます。書き込み先に同名のディレクトリがある場合など、`File.open`が失敗するときは読み込みへ進まず終了します。

現行プレビューの読者ZIPには、通常サンプル52本（import用補助モジュール1本を含む）とゲーム実習12本、PDF・README・LICENSEを収録しています。演習解答、内部の証明・テスト、編集用資料は同梱しません。

## 制作の進捗と方針

[制作ロードマップ](ROADMAP.md)に計画書から引き継いだ内容と完成条件をまとめています。
[法則から実装へ進む教材草稿](minesweeper/LESSON.md)に加え、
[ListとArrayの章別補稿](manuscript/03_ListとArrayを選ぶ.md)と
[IO・Result・Fileの章別補稿](manuscript/06_IOと失敗を読む.md)、
[第22章の確実な一手を考えるハンズオン補稿](manuscript/22_運ゲー無しを確定手から学ぶ.md)を書き進めています。
[執筆進捗と優先順位](manuscript/STATUS.md)で本文と実行サンプルの対応を管理します。
2026-10-16の本文改稿で、第3・6・13・15・17・21章の説明を増補し、
**同じTeXからPDFと学習用ZIPを再生成済み**です。
引き続き第19・20・21章を増補し、さらに第11・12章を『はじめてのBend2』と同じ
**小さなコード→実行結果→仕組みの解説→演習**の流れに沿って改稿しました。
新たに `31_image_quadrants.bend`、`32_mouse_events.bend`、
`33_nat_induction.bend` と `34_mine_mask_law.bend` を追加しました。
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
一般の隣接数の全称証明、対話式CLI、GUI実機操作の受け入れ試験とGUIの状態保存・復元は未完成です。固定CLIの操作履歴保存・復元は実装・テスト済みです。

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
`37_u32_dimension.bend`（Nat/U32変換と比較）を追加しました。

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

第10章には `44_message_boundary.bend` を追加し、`String.split` を使って区切り記号と受信単位の違いを確かめられるようにしました。その後 `47_tcp_loopback.bend` と `48_udp_loopback.bend` でローカルホストへの実際の送受信も確認できるようにしました。外部ネットワークでの運用や任意の大きさの受信は検証していません。

## 新しいゲーム実習（2026-10-17）

- `minesweeper/gui.bend` は、既存の `Start` と `Session` を利用する4×4のGUIです。左クリックで公開、右クリックで旗、`R`でリセット、`Esc`で終了します。数字は `Image` の四分木による7セグメントで表示します。Bend 2.0.37での型検査、Linuxでのネイティブビルドと13件のヘッドレス入力ロジック検証は成功しています。デスクトップ実機での目視・操作試験は別途必要です。
- `minesweeper/public_solver.bend` は、4×4・地雷2個に限定した公開情報専用の推論器です。実際の地雷位置を与えず、公開された数字と一致する120候補から確定安全マスを調べます。限定版の候補生成とゲーム上のクリック列リプレイは `minesweeper/noguess_generator.bend` に実装し、独立Pythonオラクルでも検査しました。任意のサイズ・地雷数とGUIモード連結はまだ課題です。

## 保存と運ゲー無し版の実動作（2026-10-18）

- `cli_save.bend` は初期地雷マスク33の操作履歴を `BEND2-SAVE-1|...|END` 形式で保存し、検証してから再生します。Bend File APIの実機IOと、破損・異なるバージョン・無効コマンドを拒否するテストを追加しました。GUIの現在状態を保存する機能とは異なります。
- `noguess_generator.bend` は固定の4×4・地雷2個、初手を番号0に固定した候補から、公開情報だけによる安全クリックを繰り返し、勝利まで検証できた場合だけ採用します。例はマスク `40960`、手順 `0,12,14`。独立Pythonのゲームオラクルも同じ手順を確認しました。

## 2026-10-18：第10章ループバック通信実習

- `47_tcp_loopback.bend` は`127.0.0.1`でTCPの待ち受け・接続・一文字の送受信を一つのプログラムで試し、`B`を出力します。
- `48_udp_loopback.bend` は同じコンピュータでUDPのデータグラムを送り、`BEND-UDP`を出力します。両方とも外部インターネットを使用しませんが、実行環境がローカルソケットを許可する必要があります。

## 2026-10-18：第4章のMap・Set追加実習

- `49_map_update_delete.bend`：戦績のキー上書き・削除・存在判定・サイズをまとめて実行します（結果9）。
- `50_set_from_list.bend`：重複した座標リストを集合へ変換し、削除とリストへの再変換を確かめます（結果2n）。

## 第11・12章のGUI実習を読む順序（2026-10-18）

最初に `31_image_quadrants.bend` で `Pix` / `Qua` を純粋な値として確かめ、
`23_cell_hit_test.bend` と `32_mouse_events.bend` で8×8・一マス32画素の座標変換を学びます。
その後、`minesweeper/gui.bend` の4×4・一マス64画素の変換と `App.run` / `view` / `tick` に接続します。
**8×8の学習例と4×4のゲーム実装を混同しない**ことが重要です。
GUIの13件のヘッドレス入力検査は実行済みですが、デスクトップでの目視・マウス操作とGUI状態保存は未検収です。
演習解説は `solutions/11_12_gui_exercises.md` にあり、読者ZIPには含めません。

## 第19章の追加実習（検証ブランチ）

`51_atomic_counter.bend`は`Array.atomic.add`の返り値（更新前の5）と`Array.get`で読んだ更新後の8を表示します。並列実行やGPUの速度を保証する例ではありません。本文と参考解答はそれぞれ第19章と`solutions/19_atomic_exercises.md`を参照してください。
