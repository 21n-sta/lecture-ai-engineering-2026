"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import datetime
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


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


def _learning_log_path(recorded_at: datetime) -> Path:
    return LEARNING_LOG_DIR / f"{recorded_at:%Y-%m-%d}.jsonl"


def format_learning_log(
    learned: str,
    question: str = "",
    next_action: str = "",
    lecture: int | None = None,
) -> str:
    """学習記録を承認画面と保存後の確認で使う形式に整える。"""
    return "\n".join(
        [
            f"講義回: 第{lecture}回" if lecture is not None else "講義回: 未指定",
            f"学んだこと:\n{learned.strip() or '（未記入）'}",
            f"疑問:\n{question.strip() or '（なし）'}",
            f"次にやること:\n{next_action.strip() or '（なし）'}",
        ]
    )


def format_learning_log_preview(args: dict) -> str:
    """承認前に保存先と、保存される学習記録の全文を表示する。"""
    recorded_at = datetime.now().astimezone()
    path = _learning_log_path(recorded_at)
    content = format_learning_log(**args)
    return f"保存先: {path.as_posix()}\n\n{content}"


def save_learning_log(
    learned: str,
    question: str = "",
    next_action: str = "",
    lecture: int | None = None,
) -> str:
    """項目別の学習記録を learning_log/ に追記する。実行前に利用者の承認が必要。

    学んだことは必ず記録し、疑問・次にやること・講義回は分かる範囲で指定する。
    例: 「第3回で学んだことはツール承認、疑問は承認後の再開方法、
    次にやることはCLIで試すこととして学習記録に保存して」
    """
    learned = learned.strip()
    if not learned:
        return "「学んだこと」が空のため、学習記録は保存しませんでした。"

    recorded_at = datetime.now().astimezone()
    path = _learning_log_path(recorded_at)
    record = {
        "recorded_at": recorded_at.isoformat(timespec="seconds"),
        "lecture": lecture,
        "learned": learned,
        "question": question.strip(),
        "next_action": next_action.strip(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return f"学習記録を保存しました。\n保存先: {path.as_posix()}\n\n{format_learning_log(learned, question, next_action, lecture)}"
