import unittest
from unittest.mock import patch

import app


class GeneratorContractTests(unittest.TestCase):
    def test_generate_ideas_accepts_duration_and_passes_it_through(self):
        with patch.object(app, "_configure_groq", return_value="offline"), \
             patch.object(app, "_template_ideas", return_value=["offline-idea"]) as mock_template:
            result = app.generate_ideas(
                "creator education",
                count=2,
                topic="AI productivity",
                duration="3-5min",
                content_type="Podcast",
                content_format="Interview",
                additional_context="For first-time creators",
            )

        self.assertEqual(result, ["offline-idea"])
        mock_template.assert_called_once()
        self.assertEqual(mock_template.call_args.kwargs["duration"], "3-5min")
        self.assertEqual(mock_template.call_args.kwargs["topic"], "AI productivity")
        self.assertEqual(mock_template.call_args.kwargs["content_type"], "Podcast")
        self.assertEqual(mock_template.call_args.kwargs["content_format"], "Interview")
        self.assertEqual(mock_template.call_args.kwargs["additional_context"], "For first-time creators")

    def test_generate_ideas_forwards_full_brief_to_groq_path(self):
        with patch.object(app, "_configure_groq", return_value=None), \
             patch.object(app, "_ideas_from_groq", return_value=["model-idea"]) as mock_groq:
            result = app.generate_ideas(
                "creator education",
                count=2,
                topic="AI productivity",
                platform="YouTube",
                audience="new creators",
                duration="15min+",
                content_type="Podcast",
                content_format="Interview",
                additional_context="Avoid technical jargon",
            )

        self.assertEqual(result, ["model-idea"])
        self.assertEqual(mock_groq.call_args.args[0], "creator education")
        self.assertEqual(mock_groq.call_args.kwargs["topic"], "AI productivity")
        self.assertEqual(mock_groq.call_args.kwargs["duration"], "15min+")
        self.assertEqual(mock_groq.call_args.kwargs["content_type"], "Podcast")
        self.assertEqual(mock_groq.call_args.kwargs["content_format"], "Interview")
        self.assertEqual(mock_groq.call_args.kwargs["additional_context"], "Avoid technical jargon")

    def test_idea_prompt_separates_topic_and_channel_niche(self):
        prompt = app._idea_user_prompt(
            "creator education",
            3,
            platform="YouTube",
            vibe="practical",
            audience="new creators",
            lang="en",
            variant=0,
            topic="AI productivity",
            content_type="Podcast",
            content_format="Interview",
            additional_context="Avoid technical jargon",
        )

        self.assertIn("- Topic: AI productivity", prompt)
        self.assertIn("- Channel / content niche: creator education", prompt)
        self.assertIn("- Content type: Podcast", prompt)
        self.assertIn("- Output format: Interview", prompt)
        self.assertIn("- Additional user context: Avoid technical jargon", prompt)


if __name__ == "__main__":
    unittest.main()
