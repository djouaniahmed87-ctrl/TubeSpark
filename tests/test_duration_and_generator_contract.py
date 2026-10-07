import unittest
from unittest.mock import patch

import app


class GeneratorContractTests(unittest.TestCase):
    def test_generate_ideas_accepts_duration_and_passes_it_through(self):
        with patch.object(app, "_configure_groq", return_value="offline"), \
             patch.object(app, "_template_ideas", return_value=["offline-idea"]) as mock_template:
            result = app.generate_ideas("AI productivity", count=2, duration="3-5min")

        self.assertEqual(result, ["offline-idea"])
        mock_template.assert_called_once()
        self.assertEqual(mock_template.call_args.kwargs["duration"], "3-5min")


if __name__ == "__main__":
    unittest.main()
