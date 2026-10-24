# 第21章補稿：10×10盤面をコマンドで動かしてみましょう

> **TeX本文・PDFには未統合**。この実習は固定配置の通常版を操作する途中段階です。GUI、対話入力、ファイル保存、運ゲー無し生成器はまだ接続していません。

## なぜ表示用の入口が必要なのでしょうか

前節で初手安全・0連鎖・勝敗を一つの純粋なBendエンジンにまとめました。しかし、テスト用の数値 `110` だけでは、実際にどのマスが開いたのか読者には分かりません。まずは10×10盤面を文字で表示し、クリックと旗を確かめてみましょう。

## Bendコードと実行結果

`minesweeper/nxn_cli_replay.bend` は10×10、地雷数 **M=10** の固定盤面を使います。行・列は0始まりで、セル番号は `10*y+x` です。コマンド `c0` は左上のクリック、`f1` はセル1の旗の切り替え、`r` は最初からやり直す操作です。

```bend
def replay(commands: List<String>, stage: Engine.Game) -> Engine.Game:
  match commands:
    case Nil{}:
      stage
    case command <> rest:
      replay(rest, action(stage, command))

def show_session(session: Step.Session) -> String:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      show_cells(U32.to_nat((n * n : U32)),
                 Array.to_list(Square.Square, cells), 0, n)
```

```sh
bend intermediate/minesweeper/nxn_cli_replay.bend c0 f1
```

先頭の行は `Playing`、その次の行は `1 F . . . . . . . .` になります。地雷が11番にあるため、0番を開いたときの数字は1です。旗のある1番は `F` と表示されます。残りの9行は未公開マスを `.` で表示します。

```sh
bend intermediate/minesweeper/nxn_cli_replay.bend c0 c11
```

11番は地雷なので、最初の行は `Lost` になります。その後に `f2` を追加しても、終了したゲームの盤面は変わりません。

## 仕組みを追いましょう

`Engine.Game` は地雷の真値を保持しますが、表示処理が使うのは `Step.Session` の `cells` だけです。未公開マス `Hidden` は `.`、旗 `Flag` は `F`、公開済み `Open{clue}` は数字になります。内部の地雷ビット列は表示しません。

Bendの `Array` は容量が2のべき乗へ切り上がります。10×10盤面の配列容量は128でも、`show_cells` は `n*n=100` マスだけを表示します。**余分な28要素は盤面ではありません**。コマンド列の再生は先頭から順に進み、`r` では固定配置の新しいゲームを作ります。

`scripts/test_nxn_cli_replay.py` は、Bendの実行結果である**全100マスの文字列**を、Pythonの集合・幅優先探索による独立モデルと比較します。無効添字、旗、初手の地雷移動、敗北後の入力無効、リセットも確認します。ただし、これは有限の操作列についての実行照合であり、全称証明やGUI実機検査ではありません。

## 演習

1. `c0 f1` と `c0 f1 c1` の出力を比較し、旗付きマスをクリックしても開かないことを確認してみましょう。
2. `c11` を最初の操作にした場合と、`c0 c11` の場合で結果が違う理由を説明してみましょう。
3. `c0 c11 r c0` を実行し、リセット後にもう一度遊べることを確認してみましょう。
4. 地雷数をM=5に変更するとき、盤面表示と勝利条件のどちらが変更不要か考えてみましょう。
