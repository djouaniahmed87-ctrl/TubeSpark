import unittest
from unittest.mock import patch

import app


class LandingNavigationTests(unittest.TestCase):
    def test_landing_nav_has_real_section_links(self):
        app.st.session_state.clear()
        app.st.session_state["app_mode"] = "landing"
        captured = {}

        def fake_markdown(markup, *args, **kwargs):
            captured["markup"] = markup

        with patch.object(app.st, "markdown", new=fake_markdown):
            app.inject_custom_header()

        html = captured["markup"]
        self.assertIn('href="#home"', html)
        self.assertIn('href="#tools"', html)
        self.assertIn('href="#how-it-works"', html)
        self.assertIn('href="#pricing"', html)
        self.assertIn('href="#faq"', html)


if __name__ == "__main__":
    unittest.main()
