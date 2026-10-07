import unittest

from app import CSS_TEMPLATE


class CssTemplateTests(unittest.TestCase):
    def test_font_import_is_inside_style_block(self):
        self.assertIn("<style>", CSS_TEMPLATE)
        self.assertIn("__FONT_IMPORT__", CSS_TEMPLATE)
        self.assertLess(CSS_TEMPLATE.index("<style>"), CSS_TEMPLATE.index("__FONT_IMPORT__"))
        self.assertLess(CSS_TEMPLATE.index("__FONT_IMPORT__"), CSS_TEMPLATE.index(":root"))


if __name__ == "__main__":
    unittest.main()
