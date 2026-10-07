import unittest
from unittest.mock import patch

import app
from app import CSS_TEMPLATE


class CssTemplateTests(unittest.TestCase):
    def test_font_import_is_inside_style_block(self):
        self.assertIn("<style>", CSS_TEMPLATE)
        self.assertIn("__FONT_IMPORT__", CSS_TEMPLATE)
        self.assertLess(CSS_TEMPLATE.index("<style>"), CSS_TEMPLATE.index("__FONT_IMPORT__"))
        self.assertLess(CSS_TEMPLATE.index("__FONT_IMPORT__"), CSS_TEMPLATE.index(":root"))

    def test_artifact_ui_classes_are_defined_for_generated_output(self):
        self.assertIn(".artifact-shell", CSS_TEMPLATE)
        self.assertIn(".artifact-header", CSS_TEMPLATE)
        self.assertIn(".artifact-body", CSS_TEMPLATE)
        self.assertIn(".artifact-actions", CSS_TEMPLATE)

    def test_direction_and_alignment_follow_each_language(self):
        expected = {"en": ("ltr", "left"), "fr": ("ltr", "left"), "ar": ("rtl", "right")}

        for lang, (direction, alignment) in expected.items():
            with self.subTest(lang=lang):
                with (
                    patch("app.current_lang", return_value=lang),
                    patch("app.is_rtl", return_value=direction == "rtl"),
                    patch("app.text_direction", return_value=direction),
                    patch("app.render_html") as render_html,
                ):
                    app.inject_styles()

                rendered_css = "\n".join(call.args[0] for call in render_html.call_args_list)
                self.assertIn(f"direction: {direction};", rendered_css)
                self.assertIn(f"text-align: {alignment};", rendered_css)
                self.assertNotIn("direction: rtl !important", rendered_css)

    def test_overrides_use_dark_theme_tokens(self):
        with (
            patch("app.current_lang", return_value="en"),
            patch("app.is_rtl", return_value=False),
            patch("app.text_direction", return_value="ltr"),
            patch("app.render_html") as render_html,
        ):
            app.inject_styles()

        rendered_css = "\n".join(call.args[0] for call in render_html.call_args_list)
        for token in (
            "--bg: #090D16;",
            "--surface-1: #0F1522;",
            "--surface-input: #0C121E;",
            "--text-primary: #F5F7FB;",
            "--border-default: rgba(148, 163, 184, 0.16);",
        ):
            self.assertIn(token, CSS_TEMPLATE)

        self.assertIn("background: var(--bg) !important;", rendered_css)
        self.assertIn("background: var(--bg-gradient) !important;", rendered_css)
        self.assertIn("background: var(--surface-input) !important;", rendered_css)
        self.assertIn("color: var(--text-primary) !important;", rendered_css)
        self.assertIn("border: 1px solid var(--border-default) !important;", rendered_css)
        self.assertIn("background: var(--primary-gradient) !important;", rendered_css)
        self.assertIn(".ts-hero-actions a.ts-primary-btn", rendered_css)
        self.assertIn(".ts-hero-actions a.ts-secondary-btn", rendered_css)


if __name__ == "__main__":
    unittest.main()
