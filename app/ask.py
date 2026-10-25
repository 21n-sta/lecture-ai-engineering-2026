"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 講座に固有の既定の質問をする
    uv run python -m app.ask --interactive  # 会話履歴を保って対話する

対話モードでは会話履歴を次の質問に渡し、10往復ごとに履歴を要約して短くする。
ツールを持たない「素の」呼び出しなので、講座に固有の質問には正確に答えられないことがある。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
COMPACT_EVERY = 10
COMPACTION_PROMPT = """\
これまでの会話を、次の質問に答えるための短いメモに要約してください。
ユーザーの目的・好み、確定した事実、未解決の質問や必要な文脈を残してください。
新しい質問への回答はせず、日本語で要約だけを書いてください。
"""


def _message(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part.from_text(text=text)])


def _generate(contents: list[types.Content]) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=contents)

    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        if prompt_tokens is None:
            prompt_tokens = getattr(usage, "input_token_count", "-")
        if output_tokens is None:
            output_tokens = getattr(usage, "output_token_count", "-")
        print(f"[トークン数] 入力: {prompt_tokens} / 出力: {output_tokens}")

    if response.text is None:
        raise RuntimeError("モデルからテキストの回答が返されませんでした")
    return response.text


def ask(question: str, history: list[types.Content] | None = None) -> str:
    """質問に回答する。指定された会話履歴をモデルへの入力に含める。"""
    contents = [*(history or []), _message("user", question)]
    return _generate(contents)


def compact_history(history: list[types.Content]) -> list[types.Content]:
    """会話履歴を要約し、要約だけを含む短い履歴に置き換える。"""
    summary = _generate([*history, _message("user", COMPACTION_PROMPT)])
    return [
        _message("user", f"これまでの会話の要約です。以降の質問ではこの内容を踏まえてください。\n{summary}"),
        _message("model", "要約を踏まえて、これからの質問に回答します。"),
    ]


def run_interactive(first_question: str | None = None) -> None:
    history: list[types.Content] = []
    turns_since_compaction = 0
    question = first_question.strip() if first_question is not None else None

    print("対話モードです。終了するには exit、quit、または Ctrl-D を入力してください。")
    while True:
        if question is None:
            try:
                question = input("質問> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return

        if question.lower() in {"exit", "quit", "終了"}:
            return
        if not question:
            question = None
            continue

        print(f"[質問] {question}\n")
        answer = ask(question, history)
        print(answer)
        history.extend((_message("user", question), _message("model", answer)))
        turns_since_compaction += 1

        if turns_since_compaction == COMPACT_EVERY:
            history = compact_history(history)
            turns_since_compaction = 0
            print("[会話履歴をコンパクト化しました]")

        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="会話履歴を保ちながら対話する（10往復ごとに履歴を要約）",
    )
    args = parser.parse_args()

    if args.interactive:
        print(f"[model] {MODEL}")
        try:
            run_interactive(args.question)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[model] {MODEL}")
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
