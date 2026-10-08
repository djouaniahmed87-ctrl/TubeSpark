import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import app
from streamlit.testing.v1 import AppTest


def _columns(spec, **_kwargs):
    count = spec if isinstance(spec, int) else len(spec)
    return [nullcontext() for _ in range(count)]


class InternalWorkspaceFlowTests(unittest.TestCase):
    def test_idea_generator_forwards_every_selected_generation_input(self):
        state = {}
        idea = app.Idea("Coffee workflow", "Hook", "Value")
        inputs = {
            "content_ideas_niche": "Home coffee",
            "content_ideas_audience": "New baristas",
            "content_ideas_context": "Compare affordable grinders",
        }
        selections = {
            "content_ideas_platform": "TikTok",
            "content_ideas_type": "Podcast",
            "content_ideas_duration": "15-20 min",
            "content_ideas_lang": "fr",
        }

        def text_input(_label, **kwargs):
            return inputs.get(kwargs.get("key"), "")

        def text_area(_label, **kwargs):
            return inputs.get(kwargs.get("key"), "")

        def selectbox(_label, options, **kwargs):
            selected = selections.get(kwargs.get("key"))
            return selected if selected in options else options[kwargs.get("index", 0)]

        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "tabs", return_value=[nullcontext(), nullcontext()]),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "columns", side_effect=_columns),
            patch.object(app.st, "text_input", side_effect=text_input),
            patch.object(app.st, "text_area", side_effect=text_area),
            patch.object(app.st, "selectbox", side_effect=selectbox),
            patch.object(app.st, "button", side_effect=lambda _label, **kwargs: kwargs.get("key") == "content_ideas_generate"),
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "caption"),
            patch.object(app.st, "success"),
            patch.object(app.st, "warning"),
            patch.object(app, "render_workspace_header"),
            patch.object(app, "render_platform_picker", return_value="YouTube"),
            patch.object(app, "_render_idea_result"),
            patch.object(app, "render_copy_button"),
            patch.object(app, "generate_ideas", return_value=[idea]) as generate_ideas,
        ):
            app.render_content_studio_workspace()

        generate_ideas.assert_called_once()
        self.assertEqual(generate_ideas.call_args.args[:2], ("Home coffee", app.FREE_IDEAS_COUNT))
        self.assertEqual(generate_ideas.call_args.kwargs["platform"], "TikTok")
        self.assertEqual(generate_ideas.call_args.kwargs["audience"], "New baristas")
        self.assertEqual(generate_ideas.call_args.kwargs["lang"], "fr")
        self.assertEqual(generate_ideas.call_args.kwargs["duration"], "15min+")
        self.assertIn("Podcast", generate_ideas.call_args.kwargs["vibe"])
        self.assertIn("Compare affordable grinders", generate_ideas.call_args.kwargs["vibe"])

    def test_evaluator_forwards_platform_audience_niche_type_and_title(self):
        state = {"lang": "ar"}
        result = app.Evaluation(61, 86, "Analysis", app.Idea("Improved title", "Hook", "Angle"))
        text_values = {
            "idea_eval_input": "A coffee idea for new creators",
            "idea_eval_audience": "New creators",
            "idea_eval_niche": "Coffee education",
            "idea_eval_title": "The coffee test",
        }
        options = {"idea_eval_platform": "TikTok", "idea_eval_content_type": "Podcast"}

        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "columns", side_effect=_columns),
            patch.object(app.st, "text_area", side_effect=lambda _label, **kwargs: text_values.get(kwargs.get("key"), "")),
            patch.object(app.st, "text_input", side_effect=lambda _label, **kwargs: text_values.get(kwargs.get("key"), "")),
            patch.object(app.st, "selectbox", side_effect=lambda _label, values, **kwargs: options.get(kwargs.get("key"), values[kwargs.get("index", 0)])),
            patch.object(app.st, "button", side_effect=lambda _label, **kwargs: kwargs.get("key") == "idea_eval_button"),
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "caption"),
            patch.object(app.st, "success"),
            patch.object(app.st, "warning"),
            patch.object(app, "render_workspace_header"),
            patch.object(app, "render_platform_picker", return_value="YouTube"),
            patch.object(app, "render_evaluation"),
            patch.object(app, "render_copy_button"),
            patch.object(app, "evaluate_idea", return_value=result) as evaluate,
        ):
            app.render_idea_evaluator_workspace()

        evaluate.assert_called_once()
        self.assertEqual(evaluate.call_args.args[0], "A coffee idea for new creators")
        self.assertEqual(evaluate.call_args.kwargs["lang"], "ar")
        for value in ("TikTok", "New creators", "Coffee education", "Podcast", "The coffee test"):
            self.assertIn(value, evaluate.call_args.kwargs["context"])

    def test_chat_routes_script_request_with_duration_audience_and_style(self):
        state = {"project_context": {"topic": "", "idea": "", "platform": "YouTube"}}
        script = app.Script("Coffee setup", "Description", (), (), ())
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app, "_script_from_groq", return_value=script) as generate_script,
        ):
            reply = app._chat_orchestrator(
                "Write a casual 8 minute script about home coffee for students",
                "en",
            )

        self.assertIn("shown below", reply)
        self.assertEqual(generate_script.call_args.kwargs["duration"], "8-10min")
        self.assertEqual(generate_script.call_args.kwargs["audience"], "students")
        self.assertEqual(generate_script.call_args.kwargs["vibe"], "casual")
        self.assertIn("User request:", generate_script.call_args.args[1])
        self.assertEqual(state["chat_output"]["data"], script)

    def test_chat_routes_seo_and_keeps_platform_in_generation_context(self):
        state = {"project_context": {"topic": "", "idea": "", "platform": "YouTube"}}
        seo = app.SEOData((), ("Coffee title",), (), ("0:00 - Intro",), "Description", ("coffee",))
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app, "_seo_from_groq", return_value=seo) as generate_seo,
        ):
            app._chat_orchestrator("Generate SEO about home coffee on TikTok", "fr")

        self.assertEqual(generate_seo.call_args.kwargs["lang"], "fr")
        self.assertIn("Target platform: TikTok", generate_seo.call_args.args[1])
        self.assertEqual(state["chat_output"]["data"], seo)

    def test_chat_idea_request_passes_duration_and_audience(self):
        state = {"project_context": {"topic": "", "idea": "", "platform": "YouTube"}}
        ideas = [app.Idea("Coffee idea", "Hook", "Value")]
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app, "generate_ideas", return_value=ideas) as generate_ideas,
        ):
            app._chat_orchestrator("Generate ideas about coffee for beginners 15 minutes on TikTok", "fr")

        self.assertEqual(generate_ideas.call_args.kwargs["platform"], "TikTok")
        self.assertEqual(generate_ideas.call_args.kwargs["audience"], "beginners")
        self.assertEqual(generate_ideas.call_args.kwargs["duration"], "15min+")
        self.assertEqual(generate_ideas.call_args.kwargs["lang"], "fr")

    def test_result_renderers_include_complete_script_and_seo_data(self):
        script = app.Script(
            "Coffee setup",
            "A complete description",
            ("#coffee",),
            ("coffee gear",),
            ({"name": "Opening", "time": "0:00", "content": "Open on the grinder", "notes": "Show the setup"},),
        )
        seo = app.SEOData(
            ("Brew better",),
            ("Best coffee setup",),
            ("The coffee mistake",),
            ("0:00 - Setup",),
            "SEO description",
            ("coffee setup",),
        )
        artifacts = []
        markdown = []
        with (
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "markdown", side_effect=lambda value, **_kwargs: markdown.append(value)),
            patch.object(app.st, "caption"),
            patch.object(app, "render_artifact_card", side_effect=lambda *args, **kwargs: artifacts.append((args, kwargs))),
        ):
            app._render_script_result(script, details={"duration": "8-10min", "platform": "YouTube"})
            app._render_seo_result(seo, details={"platform": "YouTube"})

        artifact_text = "\n".join(str(item) for item in artifacts)
        markdown_text = "\n".join(markdown)
        for value in ("A complete description", "Open on the grinder", "Show the setup", "coffee gear", "#coffee"):
            self.assertIn(value, artifact_text + markdown_text)
        for value in ("SEO description", "Best coffee setup", "The coffee mistake", "0:00 - Setup", "coffee setup", "Brew better"):
            self.assertIn(value, artifact_text + markdown_text)

    def test_each_internal_workspace_renders_without_exception_in_multiple_languages(self):
        workspaces = (
            ("AI Chat", "en"),
            ("Idea Generator", "fr"),
            ("Idea Evaluator", "ar"),
            ("Script Writer", "en"),
            ("SEO Optimizer", "fr"),
            ("Visual Prompt Studio", "ar"),
        )
        for workspace, lang in workspaces:
            with self.subTest(workspace=workspace, lang=lang):
                test_app = AppTest.from_file(Path(app.__file__), default_timeout=20)
                test_app.session_state["app_mode"] = "app"
                test_app.session_state["active_workspace"] = workspace
                test_app.session_state["lang"] = lang
                test_app.run()
                self.assertEqual(len(test_app.exception), 0, workspace)

    def test_language_direction_and_audio_notice_are_explicit(self):
        for lang, direction in (("en", "ltr"), ("fr", "ltr"), ("ar", "rtl")):
            with patch.object(app.st, "session_state", {"lang": lang}):
                self.assertEqual(app.text_direction(), direction)

        test_app = AppTest.from_file(Path(app.__file__), default_timeout=20)
        test_app.session_state["app_mode"] = "app"
        test_app.session_state["active_workspace"] = "AI Chat"
        test_app.session_state["lang"] = "ar"
        test_app.run()
        self.assertEqual(len(test_app.exception), 0)
        self.assertFalse(any(button.label == "🎤" for button in test_app.button))
        self.assertTrue(any("الإدخال الصوتي غير متاح" in caption.value for caption in test_app.caption))


if __name__ == "__main__":
    unittest.main()
