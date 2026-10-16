# 教材原稿案：要求を先に書き、1マスを実装する

> 今後TeXの第13・15章へ取り込むための草稿です。現行プレビューPDFには未反映です。

## 読者の疑問から始める

画面上のマスは「隠れている」「旗を置いている」「数字が見える」という
三つの状態を取ります。クリックしたときの振る舞いを、後から実装者の
判断で決めてしまうと、旗付きのマスを誤って開いたり、既に見えていた
数字を上書きしたりするかもしれません。

最初に次の表を**要件として確定**させます。

| 操作 | 入力 | 結果 |
| --- | --- | --- |
| 旗の切替 | Hidden | Flag |
| 旗の切替 | Flag | Hidden |
| 旗の切替 | Open(n) | Open(n) |
| 安全な公開 | Hidden, 隣接数n | Open(n) |
| 安全な公開 | Flag, 隣接数n | Flag |
| 安全な公開 | Open(m), 隣接数n | Open(m) |

「安全な公開」は地雷でないと盤面エンジンが確認した後の操作です。
地雷を踏む場合の状態遷移は別の要件として後から定めます。

## 1. LAWS.bendで先に宣言する

```bend
import Base
import ./game.bend as Game

law hidden_is_flagged:
  {Game.toggle_flag(Game.Hidden{}) == Game.Flag{} : Game.Square}

law opened_ignores_flag:
  for clue: U32
  {Game.toggle_flag(Game.Open{clue}) == Game.Open{clue} : Game.Square}

law flag_toggle_involution:
  for s: Game.Square
  {Game.toggle_flag(Game.toggle_flag(s)) == s : Game.Square}
```

最後の法則だけでは仕様が弱すぎます。何もしない関数も二回続ければ
元へ戻るためです。従ってHidden→FlagとFlag→Hiddenを別々の法則で
指定します。完全な7件の法則は [LAWS.bend](LAWS.bend) を参照してください。

## 2. 実装する

[game.bend](game.bend) では、`Square` を `Hidden`、
`Flag`、`Open{clue}` として定義します。
`toggle_flag` と `reveal_safe` は、副作用のない純粋関数です。

まず `reveal_safe(Open{2}, 4)` を頭の中で計算してみましょう。
新しい値で上書きするのではなく、元の `Open{2}` が残るはずです。

## 3. PROOF.bendで証明する

```bend
import Base
import ./game.bend as Game
import ./LAWS.bend as Laws

def Laws.flag_toggle_involution(s):
  match s:
    case Game.Hidden{}:
      {==}
    case Game.Flag{}:
      {==}
    case Game.Open{clue}:
      {==}
```

`match` の三分岐は、取り得るマスの状態すべてを網羅します。
`{==}` は具体例一つのテストではなく、その分岐の等式が
計算で一致することを確かめる証明です。

```sh
bend intermediate/minesweeper/game.bend
bend intermediate/minesweeper/PROOF.bend --verdict
```

`--verdict` の `ALL PROOFS CHECK` を確認します。
CIでも独立して同じ検査を行います。もしHiddenに旗を付ける
コードを何もしない処理へ変えると、二重切替の性質は保たれても
`hidden_is_flagged` に違反して証明は通りません。

## 4. 今回は何を保証したか

7件の法則が保証するのは**1マスの可視状態**です。
地雷数の算出、周囲のマス、地雷配置の保持、0の連鎖公開、
勝敗や初手安全、GUIについてはまだ保証していません。

次は盤面を表すデータ型を決め、近傍が盤面外に回り込まないという
B-01の仕様を`LAWS.bend`に定義してから実装を進めます。

**演習**：`reveal_safe(Open{1}, 3)` は何を返すでしょうか。
結果を予想してから新しい確認用コードを書き、
その振る舞いを表す法則も追加してみましょう。


## 5. 盤面の端を越えないことを先に要求する（B-01）

ここからは一つのマスだけでなく、盤面のどこにマスがあるかを考えます。
前巻のライフゲームは端が反対側へ回り込むトーラスでしたが、
マインスイーパーでは左上の (0,0) と右下の (3,3) は隣接しません。

「端の扱い」を実装者の勘で決めるのではなく、先に法則にします。

\`\`\`bend
import ./board.bend as Board

law board_no_wrap:
  {Board.neighbor(0, 0, 3, 3) == False{} : Bool}

law board_outside_x:
  for y: U32
  {Board.in_bounds(4, y) == False{} : Bool}
\`\`\`

二つ目は y の値に関係なく、4列目（0起点）は幅4の盤面外であると
主張します。特定の座標を試すだけの場合と、任意の入力について法則を
証明する場合を意識して読み比べましょう。

[board.bend](board.bend) の \`neighbor\` は、両端の座標を
\`in_bounds\` で確認してから、横差・縦差がそれぞれ1以下か、
かつ同一セルでないかを調べます。\`U32\` は符号なし整数なので、
座標を検証する前に \`x-1\` を無条件に使うと、
0の前が反対側へ見えるような誤りを招き得ます。

この実装を、4×4の各16マスから他の16マスへの**256通りの組合せ**
すべてで、独立したPythonのオラクルと比較します。
数個の \`law\` が通るだけでは拾えない実装バグを検出するためです。

## 6. 内部の正解と公開情報を分ける（B-02/B-03）

[board.bend](board.bend) には内部専用の
\`Cell{mine, square}\` 型を定義しました。地雷の真偽値と
画面に見える \`Square\` を、同じ内部レコードに格納します。
ただしソルバーへ渡せる型ではありません。ソルバーは後で
地雷の正解を含まない \`View\` 型を受け取るよう設計します。

旗の操作でも、安全なマスの公開でも、地雷の真偽値を変更する
必要はありません。そこで次のように宣言します。

\`\`\`bend
law board_toggle_keeps_mine:
  for mine: Bool
  for s: Game.Square
  {Board.mine_of(Board.toggle(Board.Cell{mine, s})) == mine : Bool}
\`\`\`

これは地雷がある場合とない場合、さらにマスの可視状態がどれであっても、
旗の切替で地雷配置の真偽値が変化しないという約束です。
\`PROOF.bend\` では \`Square\` を場合分けして証明します。

まだ盤面全体の地雷集合を表す \`Array\`／\`Set\` の不変条件には
進んでいません。\`Board.reveal\` も、呼び出し側が地雷でないことを
確認して使う低水準操作です。地雷を踏んだ際の敗北処理は、
先にG系列の法則として仕様化してから作ります。

**演習**：4×4盤面の (0,0)、(1,1)、(3,3) に
隣接するマス数をそれぞれ予想し、\`neighbor\` で確認してみましょう。
さらに、初めから公開済みのマスを公開し直しても
数字が変わらない理由を、対応する法則から説明してみましょう。
