# 第22章補稿：候補を列挙して、推測なしで勝てた盤面だけを選ぶ（PDF未統合）

公開数字から「次の安全な一手」を計算できても、すべての候補盤面を最後まで解けるとは限りません。前節の `check_candidate` は一つの盤面を検査しました。今度は、候補をいくつか作り、**実際に勝利まで到達した盤面だけを採用**してみましょう。

## まず、既存のBend版で考えてみましょう

4×4・地雷2個・初手0に限定した `intermediate/minesweeper/noguess_generator.bend` は、`consider` で候補を作り、`verified_mask` でゲームを進め、`Session.Won` に到達した候補だけを返します。公開情報ソルバーに渡すのは開いたマスの数字であり、真の地雷マスクではありません。この限定版の検証済み実行例は次のとおりです。

```sh
bend intermediate/minesweeper/noguess_generator.bend
```

```text
mines=40960;moves=0,12,14
```

では、盤面の大きさと地雷数を変える場合はどうでしょうか。Bend版N×N推論器とゲーム本体はまだ完成していません。そこで、**以下はPython参照モデルの実習**として、候補生成と検証の境界を先に確かめます。

## 候補を順番に検査してみましょう

リポジトリのルートで実行します。

```sh
PYTHONPATH=intermediate/solutions python3 - <<'PY'
from nxn_candidate_generator import generate
print(generate(4, 2, 0))
print(generate(2, 1, 0))
print(generate(4, 2, 0, max_candidates=1))
print(generate(3, 1, 4, max_frontier=0))
PY
```

```text
Generation(status='accepted', examined=3, possible=105, stuck=2, limited=0, certificate=Certificate(mines=(1, 4), clicks=(0, 2, 3), opened_count=14))
Generation(status='no_match', examined=3, possible=3, stuck=3, limited=0, certificate=None)
Generation(status='budget', examined=1, possible=105, stuck=1, limited=0, certificate=None)
Generation(status='inconclusive', examined=8, possible=8, stuck=0, limited=8, certificate=None)
```

最初の例は、初手0を安全にする地雷2個の組合せ105通りのうち、3番目で採用できる盤面を見つけています。`mines` は**生成器だけが持つ真の配置**、`clicks` は明示的な安全クリック列です。`opened_count=14` は0の連鎖公開も含むため、クリック数3とは一致しません。

## どのような仕組みでしょうか

`nxn_candidate_generator.py` は `itertools.combinations` で、初手を除いたマスから地雷位置を辞書式順序で選びます。たとえば4×4・地雷2個・初手0なら、候補数は `C(15,2)=105` です。各候補を `check_candidate` に渡し、**公開数字だけから選んだ確定安全手で勝利したときに限り**、地雷位置とクリック列を証明書として返します。推論器には真の地雷位置を渡しません。

全候補を調べても採用できなかった場合の `no_match` は、「この初手と**最小添字の確定安全手を優先する方針**では採用例がなかった」という意味です。他の安全手の選び方まで否定しません。`budget` は候補数の上限に達した状態、`inconclusive` は全候補を調べたものの推論器の探索上限に当たった状態です。どちらも「解ける盤面が存在しない証明」ではありません。`max_frontier` は連結した制約成分ごとの探索上限であり、計算量を一定に保証するものではありません。

候補を辞書式に選ぶ方法は再現性が高い反面、盤面の分布が偏ります。大きなNに対して全候補を列挙する実用的な生成器でもありません。採用された証明書は、**指定した初手・公開情報・クリック方針で勝利した有限の実行記録**です。Bend版一般化やGUIでの利用、すべての初手に対する保証はまだありません。

## 演習

まず `generate(4, 2, 0, max_candidates=2)` を実行し、3候補目まで調べないと採用されないことを確認してみましょう。次に `max_candidates=3` に変え、採用結果と `examined` の値を予想してから実行してみましょう。最後に `generate(3, 0, 0)` を試し、地雷がないときはなぜクリック1回で9マスが公開されるのか、0の連鎖公開を追って説明してみましょう。

## 検証した範囲

`tests/test_nxn_candidate_generator.py` は、2×2・3×3の全97通りの「盤面サイズ・地雷数・初手」の組合せについて、候補を順番に独立の**全盤面列挙**で検査した結果と生成器の最初の採用証明書を比較します。4×4の採用例も独立に再生し、候補数制限、推論上限、初手地雷の除外、不正入力を検査します。Pythonの有限テストであり、Bend版N×Nゲームの型検査・実行照合・形式的証明ではありません。TeX本文・PDF・読者ZIPにはまだ統合していません。
