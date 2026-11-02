# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
"config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 16,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }
- 自分で学習を実行したか（`executed_training_myself`）：はい （実行できた範囲：　）
- 学習前：`format_rate` =　0.09523809523809523 / `content_rate` =　 0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.857143
- 退行した質問：なし
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：学習していない問題の答えを断定していた
- 学習で変わったこと・変わらなかったこと：形式は統一されるようになった．内容についても基本的には参照できるようになっていた．

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：num_train_epochs を 6 に変更した
- 結果（比較表や数字）：内容の誤りが6個に増えた
- 使ったモデル・設定（`result.json` の `config` から）：
"config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 3,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 16,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }
- 自分で学習を実行したか（`executed_training_myself`）：はい （実行できた範囲：　）
- 学習前：`format_rate` =　0.09523809523809523 / `content_rate` =　 0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.7142857142857143
- ファインチューニングが向く場面・向かない場面についての考察：少ないエポック数でも形式を揃えることはできたので，回答形式を揃えるなどの作業はファインチューニングに向いていると考えられる．しかし，内容については検証用の質問を学習した質問にうまく結びつけることができていないような感じられた．学習に使う質問文と回答のセットの特徴を掴むためにはもう少し学習回数が必要だと考えられる．
