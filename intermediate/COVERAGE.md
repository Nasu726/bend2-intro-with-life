# 中級編 機能カバレッジと検証記録

本書の最優先目標は、入門編で深く扱わなかったBend 2の機能を体系的に理解し、使えるようになることです。**マインスイーパーで使用しない機能も省きません。**

この表は執筆・検証の管理記録です。単に本文に名前が出たこと、コードに掲載されたこと、型検査を通過したこと、実機動作したこと、形式的証明されたことは、それぞれ別です。

- **説明**：本文で引数・返り値・制約・使用方法に触れています。
- **例**：`intermediate/src/`にコードがあります。
- **検証**：CIが型検査・実行照合などを行います。実機のGUI・音声・ネットワークは含めません。
- **追加実習**：本の初稿ではまだAPI名と制約の説明が中心で、次の改訂で実例を補強する必要があります。

| 機能群 | 本文 | コード | 追加すべき実習・検査 |
|---|---|---|---|
| `Nat`, `U32`, `F32`, `Word`, `Cmp` | 第2章・第23章 | 他の例で一部使用 | 変換、丸め、境界値 |
| `String`, `Char` | 第2章 | `15_string_parse.bend`、Map・Setのキー | `trim`と`U32.read`を検証。split/join、文字境界は追加予定 |
| `List`, 高階関数と畳み込み | 第3章＋[詳細補稿](manuscript/03_ListとArrayを選ぶ.md)（PDFに一部反映、残りは補稿） | `03_list.bend`、`17_list_pipeline.bend` | filter/foldを実行照合。map/sortと数量指定は追加予定 |
| `Array` 操作、`fork/join/clone` | 第3章＋[詳細補稿](manuscript/03_ListとArrayを選ぶ.md)（PDFに一部反映、残りは補稿） | `18_array_mutations.bend`、`30_array_clone.bend`、前巻の基本例 | new/set/getとcloneを実行照合。fork/joinと共有時の競合は今後 |
| `Map`（文字列キー） | 第4章 | `02_map.bend`、`16_map_set_api.bend` | keysの実行照合。get欠落と順序の詳細は今後 |
| `Set` | 第4章 | `01_set.bend`、`05_marking.bend`、`16_map_set_api.bend` | 追加・重複・削除・サイズを照合 |
| `Maybe`, `Result`, `Either` | 第5・第6章 | `15_string_parse.bend`、`22_result_and_game.bend`、`25_either_case.bend` | Maybe/Result/Eitherの独立例。失敗と二者択一を区別 |
| `Pair`, `Sigma`, `Exists`, `Or` | 第5・第16章 | 追加実習 | 依存する値・存在証明 |
| `Kind`, `Quant`, 消去引数 | 第5・第16章 | 追加実習 | 型エラーとの対比 |
| `IO`, `IO.try`, `IO.die` | 第6章＋[詳細補稿](manuscript/06_IOと失敗を読む.md)（PDFに一部反映、残りは補稿） | `08_args.bend` | 失敗時の終了コード |
| `File`（文字列・バイト） | 第7章＋[IO章補稿](manuscript/06_IOと失敗を読む.md)（PDFに一部反映、残りは補稿） | `12_file_write.bend`、`13_file_read.bend` | 保存・読出し・閉鎖を実行検証、bytesは今後 |
| 引数・環境変数・乱数・時刻 | 第8章 | `08_args.bend`、`11_random_io.bend`、`19_environment.bend` | 乱数IO・環境変数の例。now/sleepは今後 |
| `Process.run` | 第8章 | `20_process_run.bend` | Linuxでの終了コード実行例。stderr・失敗は今後 |
| `IO.fork/join`, `Chan` | 第9章 | `21_io_fork.bend`、`28_chan_roundtrip.bend` | fork/joinとChan送受信・closeの実行照合。失敗・時間制限の実践は今後 |
| `IO.within`, `Poll` | 第9章 | `29_io_within.bend` | withinのSome/None処理を型検査。時間制限の実機挙動とPollは今後 |
| TCP/UDP/Socket/Listener | 第10章 | `27_tcp_connect.bend` | TCP接続の型・成功失敗分岐例。送受信・UDPループバックは今後 |
| `Image`, `Pix`, `Qua` | 第11章 | `07_gui_hello.bend` | 描画関数テスト |
| `App`, `Event`, `Window` | 第12–14章 | `07_gui_hello.bend`、`23_cell_hit_test.bend` | GUIの基本型検査・純粋な座標変換。実機入力・Windowは今後 |
| `Audio` | 第20章 | `26_audio_open.bend` | open/write/closeの型検査。実機での再生確認は今後 |
| `law`, `Equal`, 帰納法 | 第15–18章・第22章 | `04_flag_laws.bend`、`14_local_inference.bend`、`22_result_and_game.bend`、`24_bool_proofs.bend` | 全Boolについての法則と具体例を検査。依存型・補題は今後 |
| `@unsafe`, 外部信頼境界 | 第18・20章 | 追加実習 | 証明検査の境界 |
| CPU並列、GPU指定 | 第19章を増補（CPU並列・GPU指定・IO並行の比較） | `06_parallel.bend`・`21_io_fork.bend` | CPU並列の実行確認、GPU・他ターゲットでの性能と実機挙動は未検証 |
| `Array.atomic` | 第19章を増補（標準Baseの型と使用条件を説明） | 追加実習 | 呼出しコード・実機共有更新の検査は今後 |
| C/JavaScriptと外部連携 | 第20章を増補（生成ターゲットごとの検証・外部所有権を整理） | 追加実習 | 生成コードの実行テスト・FFIは今後 |
| モジュール・パッケージ | 第20章 | 追加実習 | 公開と配布 |
| 4×4盤面の近傍数 | 第13章 | `10_board_neighbors.bend` | 境界ケースと盤面全体の更新 |
| 乱数IOの失敗処理 | 第8章 | `11_random_io.bend` | 実機での失敗・再現性確認 |
| マインスイーパーの公開マス仕様 C-01〜C-07 | `intermediate/minesweeper/REQUIREMENTS.md`（第15章に一部統合） | `minesweeper/LAWS.bend`・`game.bend`・`PROOF.bend` | `--verdict`で7件の量化法則を証明。盤面・初手安全・GUIの証明ではない |
| 盤面境界・局所不変性 B-01/B-02/B-03/B-05 | `minesweeper/REQUIREMENTS.md`（第13・17章に一部統合） | `minesweeper/LAWS.bend`・`board.bend`・`PROOF.bend` | 4×4非トーラス境界と単一セルの地雷値保持・公開状態維持について9件の法則を証明。独立オラクルで全256セル対も照合。盤面全体の扱いは次行、B-04の一般全称証明は未了 |
| 16マスArray・地雷マスク・隣接地雷数・境界検査 | `minesweeper/LESSON.md`に解説草稿（第13・17章に一部統合） | `minesweeper/board4.bend`、`LAWS.bend`、`PROOF.bend` | 地雷マスク不変・空盤面の数字・具体的な数字・配列外操作の8法則を証明。Python独立オラクルで154ケースを実行。一般の隣接数の全称証明、公開時の安全判定は未完成 |
| 旗の基本操作・局所法則 | 第13・15章 | `09_minesweeper_status.bend`, `04_flag_laws.bend` | 操作の網羅 |
| クリック・旗・敗北・勝利の純粋ゲーム進行（G-02/G-03部分） | `minesweeper/LESSON.md`に追記（第17・21章に一部統合） | `minesweeper/session.bend`・`LAWS.bend`・`PROOF.bend` | 7法則を証明。独立オラクルで86件の遷移（複数クリック含む）を実行検査。初手安全・0展開・GUIは未実装 |
| プレイ可能な通常版マインスイーパー | 第21章を大幅改稿（段階的な組立て・境界条件・テスト観点） | 純粋なクリック・勝敗のみ実装、完成版は**未実装** | 初手安全、0展開、GUI、保存、実機操作の統合 |
| 運ゲー無し版 | 第22章 | `14_local_inference.bend`（局所推論）・`solutions/noguess_reference.py`（Python参考実装） | Bend版生成とGUIは未実装。Python参考実装は全列挙・失敗明示・小盤面テスト |

## CIの判定範囲

`intermediate.yml`は、上記の**存在する**Bendコードを型検査し、純粋関数のサンプルについて期待値を照合し、`law`の判定を確認します。GUIコードは型検査に限定します。XeLaTeXで原稿を組版しPDFを成果物としてアップロードします。

**未実装項目をCIの合格だけで実装済みと見なしてはいけません。** 最終的には、すべての機能群に独立して実行できる学習サンプルとテストを追加する方針です。

## 仕様の出典

- [公式GUIDE](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [公式Base](https://github.com/bendlang/bend/blob/main/bend2/base.bend)
- 現行リビジョンの固定と互換性確認は、原稿およびCIの検証環境で行います。
