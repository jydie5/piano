import os
from typing import get_type_hints

PIANO_THEORY_PROMPT = '''
ピアノコードの運指を出力してください。
以下の定義を厳密に守り、1つでも違反する場合は出力してはいけません。

【1. 音名と座標の絶対的な対応関係】
各音名は必ず以下の座標を使用すること：

白鍵（必ず is_black: false）:
1オクターブ目:
+-------+-----+------------------------+
| 音名  |  x  |      注意事項         |
+-------+-----+------------------------+
|  C    |  10 | （次のC: x=360）      |
|  D    |  60 |                       |
|  E    | 110 | 常に白鍵・変更不可    |
|  F    | 160 |                       |
|  G    | 210 |                       |
|  A    | 260 |                       |
|  B    | 310 | 常に白鍵・変更不可    |
+-------+-----+------------------------+

2オクターブ目:
+-------+-----+------------------------+
| 音名  |  x  |      注意事項         |
+-------+-----+------------------------+
|  C    | 360 |                       |
|  D    | 410 |                       |
|  E    | 460 | 常に白鍵・変更不可    |
|  F    | 510 |                       |
|  G    | 560 |                       |
|  A    | 610 |                       |
|  B    | 660 | 常に白鍵・変更不可    |
+-------+-----+------------------------+

黒鍵（必ず is_black: true）:
1オクターブ目:
+----------+-----+------------------------+
|   音名   |  x  |      注意事項         |
+----------+-----+------------------------+
| C#/Db    |  45 | 異名同音              |
| D#/Eb    |  95 | 異名同音              |
| F#/Gb    | 195 | 異名同音              |
| G#/Ab    | 245 | 異名同音              |
| A#/Bb    | 295 | 異名同音              |
+----------+-----+------------------------+

2オクターブ目:
+----------+-----+------------------------+
|   音名   |  x  |      注意事項         |
+----------+-----+------------------------+
| C#/Db    | 395 | 異名同音              |
| D#/Eb    | 445 | 異名同音              |
| F#/Gb    | 545 | 異名同音              |
| G#/Ab    | 595 | 異名同音              |
| A#/Bb    | 645 | 異名同音              |
+----------+-----+------------------------+

【2. コード種別と構成音の詳細定義】
各コードは以下の構成音で必ず構成すること：

メジャーコード（例：C）
- ルート（基音）: C
- メジャー3度（4半音上）: E （Cの場合: C→C#→D→D#→E）
- 完全5度（7半音上）: G （Cの場合: C→C#→D→D#→E→F→F#→G）

具体例：
- C: C-E-G
- G: G-B-D
- D: D-F#-A
- A: A-C#-E

マイナーコード（例：Cm）
- ルート（基音）: C
- マイナー3度（3半音上）: Eb （Cの場合: C→C#→D→Eb）
- 完全5度（7半音上）: G （Cの場合: C→C#→D→D#→E→F→F#→G）

具体例：
- Am: A-C-E
- Em: E-G-B
- Dm: D-F-A
- Gm: G-Bb-D

セブンス（例：C7）
- ルート（基音）: C
- メジャー3度（4半音上）: E
- 完全5度（7半音上）: G
- マイナー7度（10半音上）: Bb （Cの場合: C→...→Bb）

具体例：
- G7: G-B-D-F
- D7: D-F#-A-C
- A7: A-C#-E-G

メジャーセブンス（例：CM7）
- ルート（基音）: C
- メジャー3度（4半音上）: E
- 完全5度（7半音上）: G
- メジャー7度（11半音上）: B （Cの場合: C→...→B）

具体例：
- GM7: G-B-D-F#
- DM7: D-F#-A-C#
- AM7: A-C#-E-G#

マイナーセブンス（例：Cm7）
- ルート（基音）: C
- マイナー3度（3半音上）: Eb
- 完全5度（7半音上）: G
- マイナー7度（10半音上）: Bb

具体例：
- Am7: A-C-E-G
- Em7: E-G-B-D
- Dm7: D-F-A-C

【3. 運指の絶対規則】
1: 親指（通常はルート音）
2: 人差し指
3: 中指
4: 薬指
5: 小指

基本パターン：
- 三和音の場合: 1-3-5 または 1-2-3
- 四和音の場合: 1-2-3-5 または 1-2-3-4

【4. 重要な制約事項】
1. 同じ座標は絶対に2回使用しない
2. E音とB音は必ず白鍵（x=110, x=310）
3. 黒鍵の音（#,♭）は必ずis_black: true
4. 出力する座標は必ず上記の定義表のものを使用
5. 各音の役割（ルート、3度、5度、7度）は必ず説明文に含める

【5. 音程の検証ステップ】
1. ルートから各音までの半音数を数える
   - メジャー3度: 4半音
   - マイナー3度: 3半音
   - 完全5度: 7半音
   - マイナー7度: 10半音
   - メジャー7度: 11半音

2. 音程の具体例：
   Cからの場合：
   - 4半音上（M3）: C→C#→D→D#→E
   - 3半音上（m3）: C→C#→D→Eb
   - 7半音上（P5）: C→C#→D→D#→E→F→F#→G
   - 10半音上（m7）: C→...→Bb
   - 11半音上（M7）: C→...→B

【6. 完璧な出力例】
{
    "chord_name": "GM7",
    "keys": [
        {"x": 210, "is_black": false, "finger": 1, "note": "G"},    // ルート
        {"x": 310, "is_black": false, "finger": 2, "note": "B"},    // M3
        {"x": 60, "is_black": false, "finger": 3, "note": "D"},     // P5
        {"x": 195, "is_black": true, "finger": 5, "note": "Fs"}     // M7
    ],
    "explanation": "GM7の運指は1-2-3-5を使用します。G（ルート）、B（メジャー3度）、D（完全5度）、F#（メジャー7度）の配置に合わせています。この運指により、次のコードへの移動がスムーズになります。"
}

【7. 鍵盤の実際の配置】
一オクターブの配置:
白鍵: □  黒鍵: ■

■ ■   ■ ■ ■   
□□□□□□□□
C D E F G A B C
↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
10 60 110 160 210 260 310 360

【8. 出力データの検証チェックリスト】
1. コード名と構成音の確認
   □ コードの種類（M, m, 7, M7, m7）は正しいか
   □ 各構成音が理論的に正しいか
   □ 半音数は定義通りか

2. 座標値の確認
   □ 各音の座標が正しいテーブルの値と一致するか
   □ 同じ座標が重複使用されていないか
   □ E音とB音が正しく白鍵（x=110, x=310）として扱われているか
   □ 黒鍵の音に正しくis_black: trueが設定されているか

3. 運指の確認
   □ 基本パターン（1-3-5, 1-2-3, 1-2-3-5, 1-2-3-4）に従っているか
   □ 運指番号が1-5の範囲内か
   □ ルート音に1（親指）が使われているか

4. 説明文の確認
   □ 全ての音の役割（ルート、3度、5度、7度）が含まれているか
   □ コード名が正しく記載されているか
   □ 運指の説明が含まれているか

この仕様に完全に従った出力のみを生成してください。
一つでも違反する場合は、出力を中止して修正してください。
各コードを生成する前に、必ずチェックリストの全項目を確認してください。

【9. 演奏効率の最適化規則】
1. 転回位置の選択基準
   □ 最も低い位置（x座標が小さい）のCを優先して使用
   □ 手の形が自然になるよう、構成音を近い位置に配置

2. 音の配置順序
   - 基本形での推奨配置例：
     * Am: A(260) - C(10) - E(110)
     * C: C(10) - E(110) - G(210)
     * G: G(210) - B(310) - D(60)

3. 説明文での音の役割記載順序
   □ 常にルート→3度→5度（→7度）の順で記載
   □ 実際の演奏位置と説明順序が異なってもよい

4. バリデーション項目
   □ 手の大きさを考慮した鍵盤間隔の確認
   □ 黒鍵と白鍵の組み合わせによる演奏性の確認
   □ 次のコードへの移行のしやすさの確認
   
【10. セブンスコードの絶対配置ルール】
1. 7度音の配置座標の絶対規則
   ！！重要！！
   - すべての構成音は必ずルート音より高い位置に配置すること
   - 特に以下の配置を厳守：
     * ルート音がG(x=210)の場合：D(410)とF(510)を使用
     * D(60)やF(160)は使用禁止（ルートより低いため）

2. セブンスコードの正しい配置例
   正しい配置:
   - Dm7: D(60) - F(160) - A(260) - C(360)
   - D7: D(60) - F#(195) - A(260) - C(360)
   - C7: C(10) - E(110) - G(210) - Bb(295)
   - G7: G(210) - B(310) - D(60) - F(160)
   - Am7: A(260) - C(10) - E(110) - G(210)

   誤りの配置（禁止）:
   - Dm7: D(60) - F(160) - A(260) - C(10)    ← Cが下にあるため不可
   - G7: G(210) - B(310) - D(60) - F(10)     ← Fが下にあるため不可

3. セブンスコードの運指規則
   必ず以下の運指パターンを使用:
   - 1: ルート音（必須）
   - 2: 3度音
   - 3: 5度音
   - 5: 7度音（注：4は使用しない）

4. 検証項目（すべて満たすこと）
   □ 7度音はルート音より高い位置にあるか
   □ 運指は1-2-3-5のパターンになっているか
   □ すべての音が適切な間隔で配置されているか
   □ 次のコードへの移行が自然か
   □ 手の形が演奏しやすい配置か

【11. 構成音の位置関係の絶対規則】

1. 基本配置ルール
   - すべての構成音は、原則としてルート音と同じか高い位置に配置する
   - 特に7度音は必ずルート音より高い位置を使用する

2. 各コードの標準位置（例）
   Em7の場合:
   - ルート: E(110)
   - m3: G(210)
   - P5: B(310)
   - m7: D(360) ※D(60)は使用禁止

3. 転回位置を使用する場合の規則
   - 次のオクターブの音を使用：
     * C → C(360)
     * D → D(360)
     * E → E(460)
     * F → F(460)
     * G → G(560)
     等

4. 検証項目
   □ 7度音がルート音より下に配置されていないか
   □ 構成音が適切な範囲内に収まっているか
   □ 手の移動が最小限で済む配置か

【12. 9thコードの定義と配置規則】
1. 9thコードの構成音（必須）
   - ルート音
   - メジャー3度（4半音上）
   - 完全5度（7半音上）
   - マイナー7度（10半音上）
   - メジャー9度（14半音上 = 1オクターブ + 全音）

2. 基本的な配置例
   C9の場合:
   - C(10) : ルート
   - E(110) : M3
   - G(210) : P5
   - Bb(295) : m7
   - D(360) : M9

3. 運指と配置の規則
   □ 基本は1-2-3-4-5を使用
   □ 9度音は必ずルート音より1オクターブ以上上の音を使用
   □ 5音省略可（ルート、3度、7度、9度を優先）
   

【運指の補足規則】
1. 手首の自然な角度を考慮した運指
   - 低い位置から高い位置に向かって演奏する場合: 1-2-3-5
   - 高い位置から低い位置に向かって演奏する場合: 5-3-2-1

2. Am7の標準的な運指例:
   - A(260): 5（小指）
   - C(10): 3（中指）
   - E(110): 2（人差し指）
   - G(210): 1（親指）

3. 運指選択の基準
   □ 手首が不自然に曲がっていないか
   □ 指が極端に折れる配置になっていないか
   □ 次のコードへの移動がスムーズか


【コード配置の基本規則】
1. 基本配置
   □ ルート音から右側に向かって構成音を配置することを優先
   □ 特に3和音の場合は、左から右への自然な流れを重視

これらの規則に一つでも違反する場合は、たとえ音程関係が正しくても出力してはならない。

'''

def get_chord_theory_prompt() -> str:
    """ピアノコード理論のプロンプトを返す"""
    return PIANO_THEORY_PROMPT