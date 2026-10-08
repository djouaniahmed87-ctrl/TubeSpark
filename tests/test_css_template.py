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

    def test_workspace_header_uses_soft_surface_and_language_alignment(self):
        with patch("app.st.markdown") as markdown:
            app.render_workspace_header("Workspace", "Description")

        rendered_header = markdown.call_args.args[0]
        self.assertIn('class="ts-workspace-header"', rendered_header)
        self.assertIn('class="ts-workspace-title"', rendered_header)
        self.assertIn('class="ts-workspace-description"', rendered_header)
        self.assertIn("text-align: __ALIGN__;", CSS_TEMPLATE)
        self.assertIn("background: linear-gradient(120deg, rgba(139, 92, 246, 0.07), var(--surface-3) 42%, var(--surface-2));", CSS_TEMPLATE)

    def test_workspace_inputs_use_soft_surface_and_violet_focus(self):
        self.assertIn("--surface-input: #1B2940;", CSS_TEMPLATE)
        self.assertIn('div[data-testid="stSelectbox"] [role="group"]:focus-within', CSS_TEMPLATE)
        self.assertIn('div[data-testid="stMultiSelect"] [role="group"]:focus-within', CSS_TEMPLATE)
        self.assertIn("border-color: rgba(167, 139, 250, 0.58) !important;", CSS_TEMPLATE)
        self.assertIn("0 0 14px rgba(139, 92, 246, 0.08)", CSS_TEMPLATE)
        self.assertIn("div[data-testid=\"stTextInput\"]:focus-within input", CSS_TEMPLATE)
        self.assertIn("div[data-testid=\"stTextArea\"] textarea", CSS_TEMPLATE)
        self.assertIn(".ts-input-container:focus-within", CSS_TEMPLATE)

    def test_landing_container_surfaces_remain_on_original_palette(self):
        self.assertIn("--surface-1: #121A29;", CSS_TEMPLATE)
        self.assertIn("--surface-2: #192438;", CSS_TEMPLATE)
        self.assertIn("--surface-3: #202D43;", CSS_TEMPLATE)
        self.assertIn("--card-bg: var(--surface-1);", CSS_TEMPLATE)
        self.assertIn(".premium-card {\n    background: var(--surface-1);", CSS_TEMPLATE)
        self.assertIn(".ts-pricing-card {\n    background: var(--surface-1);", CSS_TEMPLATE)
        self.assertIn(".ts-proof {\n    text-align: center;\n    margin-bottom: 2rem;\n    padding: 1rem;\n    background: rgba(30, 41, 59, 0.4);", CSS_TEMPLATE)
        self.assertIn(
            ".ts-hero .accent {\n    color: var(--primary-hover);\n    background: linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%);",
            CSS_TEMPLATE,
        )
        self.assertIn(".ts-script-result {\n    background: var(--surface-1);", CSS_TEMPLATE)
        self.assertIn(".ts-seo-result {\n    background: var(--surface-1);", CSS_TEMPLATE)

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
            "--surface-1: #121A29;",
            "--surface-2: #192438;",
            "--surface-3: #202D43;",
            "--surface-input: #1B2940;",
            "--text-primary: #F5F7FB;",
            "--border-default: rgba(148, 163, 184, 0.18);",
            "--primary-soft: rgba(139, 92, 246, 0.10);",
        ):
            self.assertIn(token, CSS_TEMPLATE)

        self.assertIn("background: var(--bg) !important;", rendered_css)
        self.assertIn("background: var(--bg-gradient) !important;", rendered_css)
        self.assertIn("background: var(--surface-input) !important;", rendered_css)
        self.assertIn("color: var(--text-primary) !important;", rendered_css)
        self.assertIn("border: 1px solid rgba(167, 139, 250, 0.24) !important;", rendered_css)
        self.assertIn("background: var(--primary-gradient) !important;", rendered_css)
        self.assertIn(".ts-hero-actions a.ts-primary-btn", rendered_css)
        self.assertIn(".ts-hero-actions a.ts-secondary-btn", rendered_css)
        self.assertIn(".st-key-app_navigation", rendered_css)
        self.assertIn(".st-key-lang [role=\"radiogroup\"]", rendered_css)
        self.assertIn(".stApp:has(#home) .premium-card", rendered_css)
        self.assertIn("@media (max-width: 768px)", rendered_css)
        self.assertIn("@media (max-width: 520px)", rendered_css)


if __name__ == "__main__":
    unittest.main()
