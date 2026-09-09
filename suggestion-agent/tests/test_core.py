import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent.config import AgentSettings
from agent.core import SuggestionAgent
from schemas.pydantic_schemas import SuggestionOutputSchema, VibeAnalysisSchema


class FakeModel:
    def with_structured_output(self, schema: type[SuggestionOutputSchema]):
        from langchain_core.runnables import RunnableLambda

        def analyze(_: object) -> SuggestionOutputSchema:
            return SuggestionOutputSchema(
                email_id="ignored-by-agent",
                sender_name="Jordan",
                sender_email="jordan@example.com",
                category="feature_request",
                suggested_action="Add CSV export.",
                vibe=VibeAnalysisSchema(
                    primary_vibe="enthusiastic",
                    urgency_level="medium",
                    communication_style="constructive",
                    tags=["power_user"],
                ),
                draft_reply="Thanks for the thoughtful suggestion.",
                timestamp=1735689600,
            )

        return RunnableLambda(analyze)


class SuggestionAgentTests(unittest.TestCase):
    def test_maps_structured_output_to_shared_protobuf(self) -> None:
        settings = AgentSettings(
            model_api_key="test-key",
            model_provider="openai",
        )
        agent = SuggestionAgent(settings=settings, model_factory=lambda **_: FakeModel())

        result = agent.process(
            email_id="email-123",
            sender_email="jordan@example.com",
            email_body="Please add CSV export.",
        )

        self.assertEqual(result.email_id, "email-123")
        self.assertEqual(result.original_message.email_id, "email-123")
        self.assertEqual(result.original_message.sender_email, "jordan@example.com")
        self.assertEqual(result.original_message.body, "Please add CSV export.")
        self.assertEqual(result.vibe.tags, ["power_user"])
        self.assertEqual(result.suggested_action, "Add CSV export.")


if __name__ == "__main__":
    unittest.main()
