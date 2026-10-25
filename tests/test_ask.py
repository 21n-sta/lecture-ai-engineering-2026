from google.genai import types

import app.ask as ask_module


def test_ask_sends_history_before_the_new_question(monkeypatch):
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text="最初の質問")]),
        types.Content(role="model", parts=[types.Part.from_text(text="最初の回答")]),
    ]
    captured = []
    monkeypatch.setattr(
        ask_module,
        "_generate",
        lambda contents: captured.extend(contents) or "次の回答",
    )

    assert ask_module.ask("続きの質問", history) == "次の回答"
    assert captured[:2] == history
    assert captured[2].role == "user"
    assert captured[2].parts[0].text == "続きの質問"


def test_compact_history_replaces_full_conversation_with_summary(monkeypatch):
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text="質問")]),
        types.Content(role="model", parts=[types.Part.from_text(text="回答")]),
    ]
    captured = []
    monkeypatch.setattr(
        ask_module,
        "_generate",
        lambda contents: captured.extend(contents) or "会話の要約",
    )

    compacted = ask_module.compact_history(history)

    assert captured[:2] == history
    assert ask_module.COMPACTION_PROMPT in captured[-1].parts[0].text
    assert len(compacted) == 2
    assert "会話の要約" in compacted[0].parts[0].text
    assert compacted[1].role == "model"


def test_interactive_mode_compacts_after_ten_turns(monkeypatch):
    questions = [f"質問{i}" for i in range(1, 12)] + ["exit"]
    monkeypatch.setattr("builtins.input", lambda _: questions.pop(0))
    ask_histories = []
    compacted_histories = []

    def fake_ask(question, history):
        ask_histories.append((question, list(history)))
        return f"回答: {question}"

    def fake_compact(history):
        compacted_histories.append(list(history))
        return [
            types.Content(role="user", parts=[types.Part.from_text(text="要約")]),
            types.Content(role="model", parts=[types.Part.from_text(text="了解")]),
        ]

    monkeypatch.setattr(ask_module, "ask", fake_ask)
    monkeypatch.setattr(ask_module, "compact_history", fake_compact)

    ask_module.run_interactive()

    assert len(ask_histories) == 11
    assert len(compacted_histories) == 1
    assert len(compacted_histories[0]) == 20
    assert len(ask_histories[9][1]) == 18
    assert ask_histories[10][1][0].parts[0].text == "要約"
