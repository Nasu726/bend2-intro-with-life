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
