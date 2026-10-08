import unittest
from contextlib import nullcontext
from unittest.mock import patch

import app


class AIBrainContractTests(unittest.TestCase):
    def test_requested_duration_preserves_fifteen_minutes(self):
        self.assertEqual(
            app._chat_requested_duration("Write a script that is 15 minutes long", "8-10min"),
            "15min+",
        )
        self.assertEqual(
            app._chat_requested_duration("Write a 15-20 minute script", "8-10min"),
            "15min+",
        )
        self.assertEqual(
            app._chat_requested_duration("Make this 60 seconds", "8-10min"),
            "shorts",
        )

    def test_offline_evaluation_uses_weighted_criteria_without_fixed_bonus(self):
        with patch.object(app, "_configure_groq", return_value="offline"):
            result = app.evaluate_idea("A practical coffee brewing comparison for beginners", lang="en")

        self.assertEqual(result.score_basis, "heuristic")
        self.assertEqual(result.score, app._weighted_evaluation_score(result.criterion_scores))
        self.assertEqual(
            result.improved_score,
            app._weighted_evaluation_score(result.improved_criterion_scores),
        )
        self.assertTrue(result.criterion_scores)
        self.assertTrue(result.improved_criterion_scores)

    def test_chat_keeps_topic_and_niche_separate_and_persists_generated_artifact(self):
        state = {"project_context": {}}
        idea = app.Idea("Eco packaging test", "Compare two supplied packages", "Show the observed differences")
        classification = {
            "intents": ["IDEATE"],
            "topic": "eco packaging",
            "niche": "sustainable skincare",
            "audience": "first-time founders",
            "platform": "YouTube",
            "duration": "15min+",
            "content_type": "video",
            "format": "long-form",
            "vibe": "practical",
            "preferences": [],
            "source": "model",
        }
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app, "_classify_chat_intent", return_value=classification),
            patch.object(app, "_configure_groq", return_value="offline"),
            patch.object(app, "generate_ideas", return_value=[idea]) as generate_ideas,
        ):
            app._chat_orchestrator("Generate an idea about eco packaging", "en")

        self.assertEqual(generate_ideas.call_args.args[0], "sustainable skincare")
        self.assertEqual(generate_ideas.call_args.kwargs["topic"], "eco packaging")
        self.assertEqual(generate_ideas.call_args.kwargs["duration"], "15min+")
        self.assertEqual(generate_ideas.call_args.kwargs["audience"], "first-time founders")
        self.assertEqual(state["project_context"]["niche"], "sustainable skincare")
        self.assertEqual(state["project_context"]["topic"], "eco packaging")
        self.assertEqual(state["chat_output"]["kind"], "ideas")
        self.assertEqual(state["chat_response"]["artifacts"]["ideas"][0]["title"], idea.title)
        self.assertEqual(state["project_context"]["last_artifact"]["kind"], "ideas")

    def test_research_response_discloses_unavailable_retrieval(self):
        with patch.object(app, "_groq_json") as groq_json:
            response = app._brain_general_response("Find current trends", "en", "RESEARCH", {})

        groq_json.assert_not_called()
        self.assertEqual(response["source"], "no_retrieval")
        self.assertIn("no web or retrieval source is connected", response["answer"])

    def test_local_intent_router_supports_chained_and_contextual_requests(self):
        chained = app._rule_classify_chat_intent("Generate ideas and evaluate the best one about coffee")
        follow_up = app._rule_classify_chat_intent("Rewrite it", {"last_artifact": {"kind": "ideas"}})

        self.assertEqual(chained["intents"], ["IDEATE", "EVALUATE"])
        self.assertEqual(follow_up["intents"], ["REWRITE"])

    def test_model_intent_router_preserves_explicit_niche_slot(self):
        model_result = {
            "intents": ["IDEATE"],
            "topic": "eco packaging",
            "niche": "sustainable skincare",
            "audience": "first-time founders",
            "platform": "YouTube",
            "duration": "15min+",
            "content_type": "video",
            "format": "long-form",
            "vibe": "practical",
            "preferences": [],
        }
        with (
            patch.object(app, "_configure_groq", return_value=None),
            patch.object(app, "_groq_json", return_value=model_result),
        ):
            slots = app._classify_chat_intent("Generate an idea about eco packaging", "en", {}, [])

        self.assertEqual(slots["topic"], "eco packaging")
        self.assertEqual(slots["niche"], "sustainable skincare")
        self.assertEqual(slots["duration"], "15min+")

    def test_chat_rewrite_persists_the_revised_asset_as_project_memory(self):
        state = {
            "project_context": {
                "topic": "home coffee",
                "niche": "coffee education",
                "script": "Old draft",
                "last_artifact": {"kind": "script", "data": {"title": "Old draft"}},
            }
        }
        classification = {
            "intents": ["REWRITE"],
            "topic": "home coffee",
            "niche": "coffee education",
            "source": "model",
        }
        rewritten_script = {
            "title": "A practical home coffee guide",
            "description": "A grounded guide to brewing coffee at home.",
            "hashtags": ["coffee"],
            "keywords": ["home coffee"],
            "sections": [{"name": "Setup", "time": "0:00", "content": "Show the setup.", "notes": ""}],
        }
        model_response = {
            "intent": "REWRITE",
            "answer": "The revised script is ready.",
            "analysis": "Kept the original topic and constraints.",
            "artifacts": {"script": rewritten_script},
            "actions": ["open_script_writer"],
        }
        with (
            patch.object(app.st, "session_state", state),
            patch.object(app, "_classify_chat_intent", return_value=classification),
            patch.object(app, "_configure_groq", return_value=None),
            patch.object(app, "_groq_json", return_value=model_response),
        ):
            app._chat_orchestrator("Rewrite it more clearly", "en")

        context = state["project_context"]
        self.assertEqual(context["script"], rewritten_script["description"])
        self.assertEqual(context["script_artifact"]["title"], rewritten_script["title"])
        self.assertEqual(context["last_artifact"]["kind"], "script")
        self.assertEqual(context["last_artifact"]["data"], rewritten_script)
        self.assertEqual(state["chat_response"]["artifacts"]["script"], rewritten_script)

    def test_structured_chat_contract_rejects_non_json_artifact_values(self):
        with self.assertRaises(app.GroqFormatError):
            app._validate_chat_response({
                "intent": "GENERAL_CHAT",
                "answer": "Done.",
                "artifacts": {"unsupported": object()},
            })

    def test_rewritten_chat_artifacts_offer_the_matching_workspace_actions(self):
        labels = []
        response = {
            "answer": "The revised script is ready.",
            "analysis": "",
            "facts": [],
            "inferences": [],
            "assumptions": [],
            "score": None,
            "source": "model",
            "artifacts": {"script": {"title": "Coffee basics", "sections": []}},
        }
        output = {"kind": "context", "request": "Rewrite the script", "data": {}}
        with (
            patch.object(app.st, "session_state", {}),
            patch.object(app.st, "container", return_value=nullcontext()),
            patch.object(app.st, "expander", return_value=nullcontext()),
            patch.object(app.st, "columns", side_effect=lambda count, **_kwargs: [nullcontext() for _ in range(count)]),
            patch.object(app.st, "button", side_effect=lambda label, **_kwargs: labels.append(label) or False),
            patch.object(app.st, "markdown"),
            patch.object(app.st, "caption"),
            patch.object(app.st, "write"),
            patch.object(app.st, "json"),
            patch.object(app.st, "metric"),
            patch.object(app, "render_copy_button"),
            patch.object(app, "t", side_effect=lambda key, **_kwargs: key),
        ):
            app._render_chat_output(output, response)

        self.assertIn("Open in Script Writer", labels)
        self.assertIn("Optimize SEO", labels)


if __name__ == "__main__":
    unittest.main()
