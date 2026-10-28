# 第21章補稿：初手が確定してから地雷を生成する

## 必要性

最初の有効な左クリックを必ず安全にするため、正式な新規ゲームではクリック前に地雷位置・地雷集合を生成しません。先に配置してから地雷を移動する方式は、低レベルのテスト用部品としてのみ残します。

`nxn_lazy_game.bend`の`Fresh{n, mine_count, seed}`は生成条件だけを持ちます。右クリックや盤外クリックでは`Fresh`のままです。最初の有効な左クリックが決まってから`nxn_lazy_placement.bend`がそのセルを除外し、初めて`MineWords`を作ります。

## Bendコードと実行結果

```bend
import Base
import ./nxn_lazy_game.bend as Game

def main() -> U32:
  game = Game.new(2, 3, 0)
  game = Game.mark(game, 0)
  game = Game.click(game, 0)
  Game.snapshot(game, 0)
```

`bend intermediate/minesweeper/nxn_lazy_game.bend`の期待出力は`113`です。2×2の3地雷では初手の0番だけが安全で、数字3を表示してその場で勝利します。`100`は勝利、`13`は公開した数字3の符号です。

## 仕組み

残り候補`slots`個と残り地雷`left`個を持ち、初手以外のマスを走査します。`draw % slots < left`なら地雷にし、`left`を1減らします。候補数は毎回1減るので、最後に`slots = left = 0`となり、指定個数だけを置けます。初手の位置では乱数を進めず、地雷ビットも変更しません。

32ビット線形合同法は再現性を重視した教材用疑似乱数です。乱数品質や運ゲー無し生成を保証しません。運ゲー無しの判定には、公開数字だけから確実な手で最後まで解けるかという別の検査が必要です。

## 演習

`Game.new(3, 2, 42)`から8番を開き、`snapshot`を確かめてみましょう。初手前の`mark`、無効なクリック、`mine_count = n*n`の場合を試し、どれも地雷を生成しない理由を説明してみましょう。

**検証境界**：有限のBend型検査・実行と独立Python集合/BFSモデルの照合を追加します。N=100のGUI実機、一般運ゲー無し生成、乱数品質、既存4×4 GUIの移行は未検収。旧`start.bend`・`nxn_full_game.bend`は事前配置を渡す低レベル検証用部品です。この補稿はまだTeX/PDF/読者ZIPに統合していません。
