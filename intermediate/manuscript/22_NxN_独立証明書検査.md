# 第22章補稿：生成した盤面を別の計算方法で検査する（PDF未統合）

盤面を生成したプログラムが「推測なしで勝てた」と報告しても、そのプログラムと同じ推論器で再検査しただけでは、同じ誤りを見逃すおそれがあります。そこで、**生成器・ゲーム状態モデル・境界成分DPのいずれも使わない**独立した検査器を用意しました。

## 既存のBendコードと、今回の検査器

Bendの限定版 `minesweeper/noguess_generator.bend` は4×4・地雷2個・初手0の候補を検査します。一方、今回の `scripts/verify_nxn_certificate.py` は **Python製の独立検査器** です。一般N×NのBendソルバーが完成したという意味ではありません。

```sh
PYTHONPATH=intermediate/scripts python3 - <<'PY'
from verify_nxn_certificate import audit
print(audit(4, (1, 4), 0, (0, 2, 3), 14))
print(audit(4, (1, 4), 0, (0, 2), 14))
print(audit(4, (1, 4), 0, (0, 2, 3), 14, max_hypotheses=1))
PY
```

```text
Audit(status='valid', checked_clicks=3, opened_count=14, reason='')
Audit(status='invalid', checked_clicks=2, opened_count=2, reason='opened count mismatch')
Audit(status='limit', checked_clicks=1, opened_count=1, reason='hypothesis budget')
```

## なぜ別の方法で確かめられるのでしょうか

検査器は地雷位置から**独立に**8近傍の数字と0の連鎖公開を計算します。初手だけは、あらかじめ安全と指定したマスを開きます。2手目以降は、その時点で公開されている数字と総地雷数に整合する地雷配置を、未公開マスから**盤面全体で全列挙**します。整合するどの配置にも地雷がないマスだけを安全とし、最小添字を選ぶ方針も照合します。最後に全安全マスの公開と公開数の一致を確認します。

この方法は境界成分分割・前後DPを使わないため、実装上の共通原因による誤りを減らせます。ただし、列挙数は `C(未公開マス数, 地雷数)` で増大します。上限を超えたときの `limit` は**検証不能**であって成功ではありません。したがって、大盤面の任意の証明書を効率的に検証できると主張しません。

## 演習

クリック列を `(0, 3, 2)` に変え、なぜ不合格になるか調べてみましょう。次に `opened_count` を13に変え、実際の0連鎖による公開数と比較してみましょう。最後に `max_hypotheses=1` の結果を見て、「反例が見つかった」と「調べきれなかった」の違いを説明してみましょう。

## 検証範囲

`tests/test_verify_nxn_certificate.py` の6テストは、4×4既知証明書、地雷0、100×100の地雷ほぼ満杯の境界、偽造・未完了・誤った順序、入力契約、列挙上限を確認します。有限のPython検証であり、Bendの一般N×N実装・GUI実機・形式的全称証明ではありません。TeX/PDF/読者ZIPへは未統合です。
