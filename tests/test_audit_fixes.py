import unittest
from contextlib import nullcontext
from unittest.mock import patch

import app


class AuditFixTests(unittest.TestCase):
    def test_script_writer_uses_topic_when_title_and_project_idea_are_empty(self):
        self.assertEqual(app._script_idea_seed("", "", "A standalone topic"), "A standalone topic")

    def test_seo_inputs_are_forwarded_in_generation_context(self):
        topic, context = app._seo_generation_inputs(
            title="Working title",
            description="Existing description",
            niche="Education",
            primary_keyword="study skills",
            audience="College students",
            platform="YouTube",
        )

        self.assertEqual(topic, "Working title")
        for value in ("YouTube", "Education", "Existing description", "study skills", "College students"):
            self.assertIn(value, context)

    def test_seo_title_outputs_are_rendered(self):
        data = app.SEOData(
            thumbnail_texts=(),
            seo_titles=("Search-friendly title",),
            clickbait_titles=("Curiosity title",),
            chapters=(),
        )

        with patch.object(app.st, "markdown") as markdown:
            app._render_seo_title_suggestions(data)

        rendered = "\n".join(call.args[0] for call in markdown.call_args_list)
        self.assertIn("Search-friendly title", rendered)
        self.assertIn("Curiosity title", rendered)

    def test_script_writer_generates_from_topic_without_title_or_saved_idea(self):
        script = app.Script("Generated title", "Description", (), (), ())
        state = {}
        button_calls = []

        def text_input(_label, **kwargs):
            values = {
                "script_writer_title": "Hands-on coffee setup",
                "workspace_script_topic": "A standalone topic",
                "script_writer_audience": "Home baristas",
            }
            return values.get(kwargs.get("key"), "")

        def text_area(_label, **kwargs):
            values = {
                "script_writer_key_points": "Compare two grinders",
                "script_writer_context": "Keep it budget friendly",
            }
            return values.get(kwargs.get("key"), "")

        def selectbox(_label, options, **kwargs):
            selected = {
                "script_writer_content_type": "Podcast",
                "script_writer_duration": "15+ min",
                "script_writer_vibe": "educational",
                "script_writer_language": "fr",
            }.get(kwargs.get("key"))
            return selected if selected in options else options[kwargs.get("index", 0)]

        def button(_label, **kwargs):
            button_calls.append(kwargs.get("key"))
            return kwargs.get("key") == "content_script_generate"

        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "text_input", side_effect=text_input),
            patch.object(app.st, "text_area", side_effect=text_area),
            patch.object(app.st, "selectbox", side_effect=selectbox),
            patch.object(app.st, "button", side_effect=button),
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "columns", side_effect=lambda n, **kwargs: [nullcontext() for _ in range(n)]),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "write"),
            patch.object(app.st, "success"),
            patch.object(app, "render_workspace_header"),
            patch.object(app, "render_platform_picker", return_value="YouTube"),
            patch.object(app, "render_copy_button"),
            patch.object(app, "_script_from_groq", return_value=script) as generate_script,
        ):
            app.render_script_writer_workspace()

        generate_script.assert_called_once()
        self.assertEqual(generate_script.call_args.args[0], "A standalone topic")
        self.assertEqual(generate_script.call_args.kwargs["platform"], "YouTube")
        self.assertEqual(generate_script.call_args.kwargs["vibe"], "educational")
        self.assertEqual(generate_script.call_args.kwargs["audience"], "Home baristas")
        self.assertEqual(generate_script.call_args.kwargs["duration"], "15min+")
        self.assertEqual(generate_script.call_args.kwargs["lang"], "fr")
        for value in ("Hands-on coffee setup", "Content type: Podcast", "Compare two grinders", "Keep it budget friendly"):
            self.assertIn(value, generate_script.call_args.args[1])
        self.assertEqual(state["script_result"].title, "Generated title")

    def test_seo_optimizer_forwards_fields_and_renders_backend_titles(self):
        seo_result = app.SEOData(
            thumbnail_texts=("Strong thumbnail text",),
            seo_titles=("SEO title suggestion",),
            clickbait_titles=("Curiosity title suggestion",),
            chapters=("0:00 - Intro",),
            seo_description="Optimized description",
            seo_tags=("study skills",),
        )
        state = {}
        inputs = {
            "seo_optimizer_title": "Working title",
            "seo_optimizer_niche": "Education",
            "seo_optimizer_keyword": "study skills",
            "seo_optimizer_audience": "College students",
        }
        rendered_markdown = []

        def text_input(_label, **kwargs):
            return inputs.get(kwargs.get("key"), "")

        def text_area(_label, **kwargs):
            return "Existing description" if kwargs.get("key") == "seo_optimizer_description" else ""

        def button(_label, **kwargs):
            return kwargs.get("key") == "seo_optimizer_button"

        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "tabs", return_value=[nullcontext() for _ in range(5)]),
            patch.object(app.st, "text_input", side_effect=text_input),
            patch.object(app.st, "text_area", side_effect=text_area),
            patch.object(app.st, "selectbox", side_effect=lambda _label, options, **kwargs: options[kwargs.get("index", 0)]),
            patch.object(app.st, "button", side_effect=button),
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "markdown", side_effect=lambda value, **kwargs: rendered_markdown.append(value)),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "caption"),
            patch.object(app.st, "success"),
            patch.object(app.st, "warning"),
            patch.object(app.st, "info"),
            patch.object(app, "render_workspace_header"),
            patch.object(app, "render_platform_picker", return_value="YouTube"),
            patch.object(app, "render_artifact_card") as render_artifact,
            patch.object(app, "render_copy_button"),
            patch.object(app, "_seo_from_groq", return_value=seo_result) as generate_seo,
        ):
            app.render_seo_workspace()

        generate_seo.assert_called_once()
        self.assertEqual(generate_seo.call_args.args[0], "Working title")
        context = generate_seo.call_args.args[1]
        for value in ("YouTube", "Education", "Existing description", "study skills", "College students"):
            self.assertIn(value, context)
        rendered = "\n".join(rendered_markdown)
        self.assertIn("SEO title suggestion", rendered)
        self.assertIn("Curiosity title suggestion", rendered)
        self.assertIn("Strong thumbnail text", rendered)
        self.assertTrue(any(call.args[1] == "0:00 - Intro" for call in render_artifact.call_args_list))

    def test_chat_actions_remain_available_after_message_and_action_reruns(self):
        state = {"main_ai_copilot_input": "topic: a test topic"}
        current_click = {"key": "copilot_send"}
        seen_buttons = []

        def button(_label, **kwargs):
            key = kwargs.get("key")
            seen_buttons.append(key)
            return key == current_click["key"]

        def columns(spec, **kwargs):
            count = spec if isinstance(spec, int) else len(spec)
            return [nullcontext() for _ in range(count)]

        def form_submit_button(_label, **kwargs):
            return kwargs.get("key") == current_click["key"]

        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "button", side_effect=button),
            patch.object(app.st, "columns", side_effect=columns),
            patch.object(app.st, "form", return_value=nullcontext()),
            patch.object(app.st, "form_submit_button", side_effect=form_submit_button),
            patch.object(app.st, "text_input", return_value="topic: a test topic"),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "chat_message", side_effect=lambda *_args, **_kwargs: nullcontext()),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "caption"),
            patch.object(app.st, "write"),
            patch.object(app.st, "success"),
            patch.object(app.st, "info"),
            patch.object(app.st, "rerun"),
            patch.object(app, "render_artifact_card"),
            patch.object(app, "render_copy_button"),
            patch.object(app, "_copilot_reply", return_value="A test reply"),
        ):
            app.render_ai_chat_panel()
            self.assertIn("chat_use_content_studio", seen_buttons)
            self.assertEqual(state["last_chat_reply"], "A test reply")

            seen_buttons.clear()
            current_click["key"] = "chat_use_content_studio"
            app.render_ai_chat_panel()

        self.assertEqual(state["active_workspace"], "Idea Generator")
        self.assertIn("chat_use_content_studio", seen_buttons)

    def test_stored_ai_error_is_rendered_from_the_active_app_shell(self):
        state = {"app_sidebar_open": False, "active_workspace": "AI Chat"}
        rendered_errors = []
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "columns", side_effect=lambda spec, **kwargs: [nullcontext() for _ in range(len(spec))]),
            patch.object(app.st, "button", return_value=False),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "error", side_effect=lambda message, **_kwargs: rendered_errors.append(message)),
            patch.object(app.st, "expander", return_value=nullcontext()),
            patch.object(app, "render_language_switcher"),
            patch.object(app, "render_ai_chat_workspace", side_effect=lambda: app._set_ai_error("ai.request_failed")),
            patch.object(app, "t", return_value="AI request failed"),
        ):
            app.render_app_shell()

        self.assertEqual(rendered_errors, ["AI request failed"])


if __name__ == "__main__":
    unittest.main()
