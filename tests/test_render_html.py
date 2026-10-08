import unittest
from pathlib import Path
from unittest.mock import patch

import app
from streamlit.testing.v1 import AppTest


class RenderHtmlRegressionTests(unittest.TestCase):
    def test_artifact_cards_render_through_html_helper(self):
        with patch.object(app.st, "markdown") as markdown:
            app.render_artifact_card("Artifact", "Rendered body")

        self.assertIn("Rendered body", markdown.call_args.args[0])
        self.assertTrue(markdown.call_args.kwargs["unsafe_allow_html"])

    def test_idea_cards_render_when_ideas_are_in_session_state(self):
        test_app = AppTest.from_file(Path(app.__file__), default_timeout=20)
        test_app.session_state["app_mode"] = "app"
        test_app.session_state["active_workspace"] = "Idea Generator"
        test_app.session_state["ideas"] = [
            app.Idea(
                title="A rendered idea",
                hook="A strong hook",
                value="A clear viewer benefit",
                steps=("First step",),
                tags=("creator",),
                keywords=("video ideas",),
            )
        ]
        test_app.session_state["ideas_niche"] = "Education"

        test_app.run()

        self.assertEqual(len(test_app.exception), 0)
        self.assertTrue(any("A rendered idea" in item.value for item in test_app.markdown))


if __name__ == "__main__":
    unittest.main()
