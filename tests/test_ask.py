from google.genai import types

import app.ask as ask_module


def test_ask_sends_history_before_the_new_question(monkeypatch):
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text="最初の質問")]),
        types.Content(role="model", parts=[types.Part.from_text(text="最初の回答")]),
    ]
    captured = []
    models = []

    def fake_generate(contents, model):
        captured.extend(contents)
        models.append(model)
        return "次の回答"

    monkeypatch.setattr(
        ask_module,
        "_generate",
        fake_generate,
    )

    assert ask_module.ask("続きの質問", history, "test-model") == "次の回答"
    assert models == ["test-model"]
    assert captured[:2] == history
    assert captured[2].role == "user"
    assert captured[2].parts[0].text == "続きの質問"


def test_compact_history_replaces_full_conversation_with_summary(monkeypatch):
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text="質問")]),
        types.Content(role="model", parts=[types.Part.from_text(text="回答")]),
    ]
    captured = []
    models = []

    def fake_generate(contents, model):
        captured.extend(contents)
        models.append(model)
        return "会話の要約"

    monkeypatch.setattr(
        ask_module,
        "_generate",
        fake_generate,
    )

    compacted = ask_module.compact_history(history, "test-model")

    assert models == ["test-model"]
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
    used_models = []
    compact_models = []

    def fake_ask(question, history, model):
        ask_histories.append((question, list(history)))
        used_models.append(model)
        return f"回答: {question}"

    def fake_compact(history, model):
        compacted_histories.append(list(history))
        compact_models.append(model)
        return [
            types.Content(role="user", parts=[types.Part.from_text(text="要約")]),
            types.Content(role="model", parts=[types.Part.from_text(text="了解")]),
        ]

    monkeypatch.setattr(ask_module, "ask", fake_ask)
    monkeypatch.setattr(ask_module, "compact_history", fake_compact)

    ask_module.run_interactive()

    assert len(ask_histories) == 11
    assert len(compacted_histories) == 1
    assert used_models == [ask_module.MODEL] * 11
    assert compact_models == [ask_module.MODEL]
    assert len(compacted_histories[0]) == 20
    assert len(ask_histories[9][1]) == 18
    assert ask_histories[10][1][0].parts[0].text == "要約"


def test_ask_prints_elapsed_time_and_uses_selected_model(monkeypatch, capsys):
    models = []
    clock = iter([10.0, 12.5])

    def fake_generate(contents, model):
        assert contents[-1].parts[0].text == "質問"
        models.append(model)
        return "回答"

    monkeypatch.setattr(ask_module, "_generate", fake_generate)
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(clock))

    assert ask_module.ask("質問", model="gemini-test") == "回答"

    assert models == ["gemini-test"]
    assert "[回答時間] 2.50 秒" in capsys.readouterr().out


def test_argument_parser_accepts_model_override(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["app.ask", "--model", "gemini-test", "質問"])
    monkeypatch.setattr(ask_module, "ask", lambda question, model: f"{model}: {question}")
    ask_module.main()

    output = capsys.readouterr().out
    assert "[model] gemini-test" in output
    assert "gemini-test: 質問" in output


def test_list_models_prints_models_that_support_generation(monkeypatch, capsys):
    class FakeClient:
        class models:
            @staticmethod
            def list():
                return [
                    types.Model(
                        name="models/gemini-test",
                        display_name="Gemini Test",
                        supported_actions=["generateContent"],
                    ),
                    types.Model(
                        name="models/embedding-test",
                        display_name="Embedding Test",
                        supported_actions=["embedContent"],
                    ),
                ]

    def create_client(api_key):
        assert api_key == "test-key"
        return FakeClient()

    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    ask_module.list_models()

    output = capsys.readouterr().out
    assert "models/gemini-test: Gemini Test" in output
    assert "embedding-test" not in output


def test_list_models_reports_empty_generation_model_list(monkeypatch, capsys):
    class FakeClient:
        class models:
            @staticmethod
            def list():
                return []

    def create_client(api_key):
        assert api_key == "test-key"
        return FakeClient()

    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    ask_module.list_models()

    assert "モデルが見つかりませんでした" in capsys.readouterr().out


def test_list_models_flag_exits_without_asking(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["app.ask", "--list-models"])
    monkeypatch.setattr(ask_module, "list_models", lambda: print("モデル一覧"))

    def fail_ask(question, history=None, model=ask_module.MODEL):
        raise AssertionError(f"ask should not run: {question}, {history}, {model}")

    monkeypatch.setattr(ask_module, "ask", fail_ask)

    ask_module.main()

    assert "モデル一覧" in capsys.readouterr().out
