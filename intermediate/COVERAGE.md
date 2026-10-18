# 中級編 機能カバレッジと検証記録

本書の最優先目標は、入門編で深く扱わなかったBend 2の機能を体系的に理解し、使えるようになることです。**マインスイーパーで使用しない機能も省きません。**

この表は執筆・検証の管理記録です。単に本文に名前が出たこと、コードに掲載されたこと、型検査を通過したこと、実機動作したこと、形式的証明されたことは、それぞれ別です。

- **説明**：本文で引数・返り値・制約・使用方法に触れています。
- **例**：`intermediate/src/`にコードがあります。
- **検証**：CIが型検査・実行照合などを行います。実機のGUI・音声・ネットワークは含めません。
- **追加実習**：本の初稿ではまだAPI名と制約の説明が中心で、次の改訂で実例を補強する必要があります。

| 機能群 | 本文 | コード | 追加すべき実習・検査 |
|---|---|---|---|
| `Nat`, `U32`, `F32`, `Word`, `Cmp` | 第2・23章を改稿（型を選ぶ必要性と変換を具体化） | `37_u32_dimension.bend` ほか | Nat→U32変換と大小比較を実行検査。F32/Wordの丸め・境界値は今後 |
| `String`, `Char` | 第2章を改稿（設定行の分割・数値変換） | `15_string_parse.bend`、`35_string_fields.bend` | trim/U32.readとsplitの件数を実行照合。joinと文字境界は今後 |
| `List`, 高階関数と畳み込み | 第3章を全面改稿（map/filter/sort/foldの目的と結果を比較） | `03_list.bend`、`17_list_pipeline.bend`、`38_list_sort.bend`、`40_list_map.bend` | map・sort・filter・foldを型検査と結果照合で確認。安定ソート・巨大入力性能は対象外 |
| `Array` 操作、`fork/join/clone` | 第3章を改稿（更新・to_list・cloneの用途を比較） | `18_array_mutations.bend`、`30_array_clone.bend`、`39_array_to_list.bend` | new/set/get・clone・to_listの結果を照合。共有時の競合とfork/joinの実機検証は今後 |
| `Map`（文字列キー） | 第4章を改稿（存在・既定値・上書き・削除を区別） | `02_map.bend`、`16_map_set_api.bend`、`36_map_missing.bend`、`49_map_update_delete.bend` | Map.has/get/set/del/sizeの組み合わせを実行照合。キー順と複雑な値型は今後 |
| `Set` | 第4章（重複するListとの相互変換を追加） | `01_set.bend`、`05_marking.bend`、`16_map_set_api.bend`、`50_set_from_list.bend` | 追加・重複・削除・サイズ・from_list/to_listを照合。変換後のキー順は保証しない |
| `Maybe`, `Result`, `Either` | 第5・第6章 | `15_string_parse.bend`、`22_result_and_game.bend`、`25_either_case.bend` | Maybe/Result/Eitherの独立例。失敗と二者択一を区別 |
| `Pair`, `Sigma`, `Exists`, `Or` | 第5・第16章 | `52_pair_exists.bend` | PairとExistsの構築・値の取り出しを実習。`n=2`の証拠は一般全称証明ではない。`Or`と複雑な依存型の演習は今後 |
| `Kind`, `Quant`, 消去引数 | 第5・第16章 | 追加実習 | 型エラーとの対比 |
| `IO`, `IO.try`, `IO.die` | 第6章＋[詳細補稿](manuscript/06_IOと失敗を読む.md)（PDFに一部反映、残りは補稿） | `08_args.bend` | 失敗時の終了コード |
| `File`（文字列・バイト） | 第7章と第21章（保存・復元） | `12_file_write.bend`、`13_file_read.bend`、`45_binary_file.bend`、`minesweeper/cli_save.bend` | 文字列・バイト列の保存と閉鎖、実ファイルの `00 0A 0D FF` 照合。大容量の反復読取・GUI保存は未完成 |
| 引数・環境変数・乱数・時刻 | 第8章 | `08_args.bend`、`11_random_io.bend`、`19_environment.bend`、`46_elapsed_clock.bend` | IO.now/sleepの実行検証。経過時間を固定せず数値形式を照合 |
| `Process.run` | 第8章 | `20_process_run.bend` | Linuxでの終了コード実行例。stderr・失敗は今後 |
| `IO.fork/join`, `Chan` | 第9章 | `21_io_fork.bend`、`28_chan_roundtrip.bend` | fork/joinとChan送受信・closeの実行照合。失敗・時間制限の実践は今後 |
| `IO.within`, `Poll` | 第9章（時間切れ・仕事の非取消・Ready/Waitを型に沿って解説） | `29_io_within.bend` | withinのSome/None処理は型検査済み。PollはBaseのtry_send/try_recvの返り値を解説した段階で、実行サンプルと時間制限の実機挙動は未検証 |
| TCP/UDP/Socket/Listener | 第10章（TCPとUDPのローカル送受信実習を追加） | `27_tcp_connect.bend`、`47_tcp_loopback.bend`、`48_udp_loopback.bend` | 127.0.0.1でlisten/connect/accept/send/recv、UDP.bind/send_to/recv_fromとcloseを実行検査。長文フレーミング、外部ネットワーク、UDP損失の実機検査は今後 |
| `Image`, `Pix`, `Qua` | 第11章を改稿（図・最小コード・出力・演習） | `31_image_quadrants.bend`、`07_gui_hello.bend` | 四分木の左上色を実行検査。ウィンドウ実機表示は別検査 |
| `App`, `Event`, `Window` | 第12章で8×8の座標変換から4×4 GUIのview/tick・64画素・所有権へ接続、第14・21章 | `07_gui_hello.bend`、`23_cell_hit_test.bend`、`32_mouse_events.bend`、`minesweeper/gui.bend`、`gui_smoke.bend` | 8×8の独立例、4×4 GUIの型検査・Linuxネイティブビルド・13件のヘッドレス入力検査。実機の画面操作・GUI保存は未検収 |
| `Audio` | 第20章 | `26_audio_open.bend` | open/write/closeの型検査。実機での再生確認は今後 |
| `law`, `Equal`, 帰納法 | 第15〜18章を再構成（入門的な法則→Boolの全称証明→Nat帰納法→盤面不変条件） | `04_flag_laws.bend`、`14_local_inference.bend`、`22_result_and_game.bend`、`24_bool_proofs.bend`、`33_nat_induction.bend` | Natについての帰納法を `--verdict` で新たに検査。依存型・一般の補題は今後 |
| `@unsafe`, 外部信頼境界 | 第18・20章 | 追加実習 | 証明検査の境界 |
| CPU並列、GPU指定 | 第19章を増補（CPU並列・GPU指定・IO並行の比較） | `06_parallel.bend`・`21_io_fork.bend` | CPU並列の実行確認、GPU・他ターゲットでの性能と実機挙動は未検証 |
| `Array.atomic` | 第19章（APIの返り値と更新前後の違いを実行する） | `51_atomic_counter.bend` | `Array.atomic.add`の型検査、旧値5・新値8を独立出力照合。`Array.fork`で共有した場合の競合・GPU実機動作は未検証 |
| C/JavaScriptと外部連携 | 第20章にC生成・ネイティブビルド・Node.js実行の一連の手順を追加 | `43_target_hello.bend` | CIでBend/C/JSの3実行結果42を確認。外部FFIの相互呼出し・GPU等は今後 |
| モジュール・パッケージ | 第20章に二ファイルimport演習を追加 | `board_index.bend`、`42_module_board.bend` | モジュール読み込みと計算結果を照合。BendHubへの公開・外部パッケージ依存は実施せず |
| 4×4盤面の近傍数 | 第13章 | `10_board_neighbors.bend` | 境界ケースと盤面全体の更新 |
| 乱数IOの失敗処理 | 第8章 | `11_random_io.bend` | 実機での失敗・再現性確認 |
| マインスイーパーの公開マス仕様 C-01〜C-07 | `intermediate/minesweeper/REQUIREMENTS.md`（第15章に一部統合） | `minesweeper/LAWS.bend`・`game.bend`・`PROOF.bend` | `--verdict`で7件の量化法則を証明。盤面・初手安全・GUIの証明ではない |
| 盤面境界・局所不変性 B-01/B-02/B-03/B-05 | `minesweeper/REQUIREMENTS.md`（第13・17章に一部統合） | `minesweeper/LAWS.bend`・`board.bend`・`PROOF.bend` | 4×4非トーラス境界と単一セルの地雷値保持・公開状態維持について9件の法則を証明。独立オラクルで全256セル対も照合。盤面全体の扱いは次行、B-04の一般全称証明は未了 |
| 16マスArray・地雷マスク・隣接地雷数・境界検査 | `minesweeper/LESSON.md`に解説草稿（第13・17章に一部統合） | `minesweeper/board4.bend`、`LAWS.bend`、`PROOF.bend` | 地雷マスク不変・空盤面の数字・具体的な数字・配列外操作の8法則を証明。Python独立オラクルで154ケースを実行。一般の隣接数の全称証明、公開時の安全判定は未完成 |
| 旗の基本操作・局所法則 | 第13・15・17章 | `09_minesweeper_status.bend`, `04_flag_laws.bend`, `34_mine_mask_law.bend` | 最小の地雷マスク不変と旗ビット変更を `--verdict` で検査。全盤面の他条件は別途 |
| クリック・旗・敗北・勝利の純粋ゲーム進行（G-02/G-03部分） | `minesweeper/LESSON.md`に追記（第17・21章に一部統合） | `minesweeper/session.bend`・`LAWS.bend`・`PROOF.bend` | 7法則を証明。初手と0領域の処理を別モジュールへ追加。43法則を先行宣言し、Bend検査と独立オラクルを利用。GUIの実機動作は未検証 |
| 通常版マインスイーパー（GUI統合） | 第21章にCLI・GUIの起動方法、座標とイベント、Array.clone、7セグメント描画を収録 | `minesweeper/start.bend`、`cli_replay.bend`、`gui.bend`（同じエンジン） | CLI出力、GUIの13件の純粋入力検査とLinuxのネイティブビルド成功。実機ウィンドウでのクリック試験、GUIの保存・復元は未了。固定CLI操作履歴保存は別途実装・検証済み |
| 運ゲー無し版 | 第22章に公開モデル120候補、実際に勝利まで追う限定版生成を収録 | `14_local_inference.bend`、`minesweeper/public_solver.bend`、`minesweeper/noguess_generator.bend`、`solutions/noguess_reference.py` | 公開情報だけを使うBendソルバーは独立13ケース照合、限定版生成はBendゲームで勝利しPython別実装でも `40960 / 0,12,14` を検証。Python参考検証器を全120配置・1,680件の0連鎖で独立照合し、不正公開情報と探索上限も検査。これはBendの全称証明ではない。一般サイズ・GUIへの導入は未了 |

## CIの判定範囲

`intermediate.yml`は、上記の**存在する**Bendコードを型検査し、純粋関数のサンプルについて期待値を照合し、`law`の判定を確認します。GUIコードは型検査に限定します。XeLaTeXで原稿を組版しPDFを成果物としてアップロードします。

**未実装項目をCIの合格だけで実装済みと見なしてはいけません。** 最終的には、すべての機能群に独立して実行できる学習サンプルとテストを追加する方針です。

## 仕様の出典

- [公式GUIDE](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [公式Base](https://github.com/bendlang/bend/blob/main/bend2/base.bend)
- 現行リビジョンの固定と互換性確認は、原稿およびCIの検証環境で行います。

初手安全 G-01：別モジュール `minesweeper/start.bend` で地雷配置済みの `Session.new` とプレイヤー入口を分離。先行コミットで仕様6法則を宣言した後、実装・証明。計37法則と初手178件の独立オラクルをCIで検証。一般の初手安全の全称証明やGUI上での入力は未検証。

G-04（0の連鎖公開）：`flood.bend` を `session.bend` から呼び出す方式で実装。6法則（空盤面の勝利、境界数字、地雷／旗の保護、非0非連鎖）を先行定義し、独立Python BFSを追加。停止性は`Nat`燃料と探索済みマスクで管理。一般の全称定理・GUIの実機動作は未検証。

## 2026-10-17 GUI・公開情報ソルバーの追加

- GUIは既存の`Start`・`Session`を使い、`App.run`で操作を受け取ります。色・数字は`Image`四分木に描きます。Bendの型検査とLinuxネイティブビルド、座標・状態の12例を確認しました。
- `public_solver.bend` は4×4・地雷2個の候補120通りを列挙します。入力は公開された`Number{index,clue}`のみで、真の地雷マスクは受け取りません。矛盾した公開状態を`None`にする設計で、独立オラクルをCIへ追加しました。
- GUIの実際のウィンドウ操作、保存・復元、任意個数の地雷のソルバー、盤面自動生成は未完成です。

## 2026-10-18：限定版生成とファイルIOの検証

- 公開ソルバーだけでなく `noguess_generator.bend` で候補を列挙し、`Session.Won` を実際に確認できたものだけ返す。Python独立ゲームでマスク40960・クリック列0→12→14を照合。
- `cli_save.bend` は固定マスク33のコマンド履歴を一度書き出し、別プロセスで再読込して盤面を復元。欠落ファイル、異なるバージョン、範囲外操作、終端改変、操作数超過などを拒否。
- GUIの左・右以外のボタンは無効化し、ヘッドレス検査を13項目に拡充。ウィンドウ実機試験とGUI状態の保存は未完了。
