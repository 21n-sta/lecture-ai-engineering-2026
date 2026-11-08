# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い： まとまって見やすい回答になった．
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary が query:LoRA , query:QLoRA として呼び出されていた．
- 1つの質問での LLM 呼び出し回数（`requests`）：２回
- 追加したツールと、docstring に書いた説明：make_quiz

def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように復習用の問題を求められたときに使う。
    """
    glossary = load_glossary()
    terms = [term for term in glossary if term["lecture"] == lecture]
    if not terms:
        available = sorted({term["lecture"] for term in glossary})
        lectures = ", ".join(str(number) for number in available)
        return f"第{lecture}回の用語は用語集にありません。用意されている回: {lectures}"

    term = random.choice(terms)
    return json.dumps(
        {
            "lecture": lecture,
            "question": f"「{term['definition']}」を表す用語は何でしょう？",
            "answer": term["term"],
        },
        ensure_ascii=False,
    )

## 宿題

- 取り組んだレベル：発展
- やったこと：save_learning_log を作成した
単に一文を保存するのではなく，講義回・疑問など項目別に記録するようにした．また，保存する前に保存する文章がわかるようにした．
- 結果：json 形式で保存することができた．
- 気づき・疑問：学習記録を取り出すツールがあれば項目分けした効果が実感できそう．
