# 第22章補稿：生成した候補を、別の方法で確かめる（PDF未統合）

運ゲー無し盤面の生成器が「クリアできた」と返しても、同じ推論器で確かめるだけでは共通のバグを見逃すかもしれません。そこで、候補生成と独立検査を**一つのコマンドで連続実行**してみましょう。生成器は公開数字の境界成分を使い、検査器は盤面全体の地雷配置を列挙します。どちらもPython参照実装で、BendのN×N実装が完成したわけではありません。

## 実際に動かす

リポジトリのルートで実行します。

```sh
python3 intermediate/scripts/audit_generated_nxn.py
```

結果は機械的に読み取れるJSONです。主要部分を抜き出すと、次のようになります。

```json
{
  "status": "verified",
  "generation_status": "accepted",
  "size": 4,
  "mine_count": 2,
  "first": 0,
  "possible": 105,
  "examined": 3,
  "mines": [1, 4],
  "clicks": [0, 2, 3],
  "opened_count": 14,
  "audit_status": "valid",
  "audit_checked_clicks": 3
}
```

4×4盤面で初手0を安全とし、地雷2個の候補105通りのうち3番目で盤面が見つかりました。公開情報から確定したクリック列は0、2、3で、0の連鎖公開も含め14個の安全マスを開けました。独立検査器は同じクリック列の3手を、**生成器の推論結果を使わず**に検査しています。JSONには候補が行き詰まった件数なども記録されます。

## 「盤面が見つかった」と「検査できた」は違います

独立検査の列挙上限を1にすると、結果が変わります。

```sh
python3 intermediate/scripts/audit_generated_nxn.py --max-hypotheses 1
```

```text
"generation_status": "accepted"
"audit_status": "limit"
"status": "audit_limit"
```

生成器の成功はそのままですが、独立検査は列挙を終えられませんでした。これは不正な盤面が見つかったという意味でも、正しいと証明できたという意味でもありません。コマンドの終了コードは、`verified` が0、候補なし・探索上限・検査上限が2、**不正な証明書**が3です。自動テストでは0以外を成功として扱わないようにしましょう。

候補の列挙数を1に絞ると、今度は生成側が先に止まります。

```sh
python3 intermediate/scripts/audit_generated_nxn.py --max-candidates 1
```

```text
"status": "budget"
"examined": 1
"possible": 105
```

この場合、独立検査はまだ始まっていません。`no_match` は指定した初手と最小添字優先方針で全候補を調べても採用されなかったことを表し、**ほかのクリック方針でも解けない**とは言えません。

## どのように検査を分離しているのでしょうか

`solutions/nxn_candidate_generator.py` は公開数字だけを `nxn_public_inference.py` に渡して候補をリプレイします。新しい `scripts/audit_generated_nxn.py` は、採用された地雷位置・クリック列・公開数を `verify_nxn_certificate.py` へ渡します。後者は生成器の内部状態を参照せず、公開数字と整合する地雷配置を**盤面全体から独立に列挙**し、各手が最小添字の確定安全マスであることと勝利条件を検査します。探索上限を超えた場合は必ず `audit_limit` になります。

## 演習

`--size 2 --mine-count 1` を試し、`no_match` と `verified` の違いを説明してみましょう。`--max-candidates 1` と `--max-hypotheses 1` を別々に指定し、どちらの段階で探索が止まるか比較してみましょう。最後に、`tests/test_audit_generated_nxn.py` の偽造クリック列を読み、なぜ独立検査が不正を検出できるか考えてみましょう。

## 検証範囲

新規8テストでは、4×4の既知証明書、2×2と3×3の計31条件、候補予算・独立検査予算・偽造クリック列・CLI終了コードを確認します。これは**有限のPython実行検査**です。Bend版のN×N生成器・ソルバー、任意の大盤面に対する独立検査の完走、GUI実機、形式的全称証明を保証しません。TeX/PDF/読者ZIPには未統合です。
