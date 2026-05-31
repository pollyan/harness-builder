from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from harness_builder_agent.schemas.common import Confidence


HISTORY_RECOMMENDATION_DIR = ".ai/review/workflow-routing-recommendations"


class WorkflowRecommendationHistoryEntry(BaseModel):
    recommendation_id: str
    task_id: str
    created_at: str
    yaml_path: str
    markdown_path: str
    recommended_workflow: str
    risk_level: Literal["low", "medium", "high"]
    confidence: Confidence
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"

    @model_validator(mode="after")
    def validate_review_paths(self) -> "WorkflowRecommendationHistoryEntry":
        expected_yaml = f"{HISTORY_RECOMMENDATION_DIR}/{self.recommendation_id}.yaml"
        expected_markdown = f"{HISTORY_RECOMMENDATION_DIR}/{self.recommendation_id}.md"
        if self.yaml_path != expected_yaml:
            raise ValueError("yaml_path must point to the indexed recommendation YAML")
        if self.markdown_path != expected_markdown:
            raise ValueError("markdown_path must point to the indexed recommendation Markdown")
        return self


class WorkflowRecommendationHistory(BaseModel):
    schema_version: str = "1.0"
    latest_recommendation_id: str | None = None
    recommendations: list[WorkflowRecommendationHistoryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_latest_recommendation(self) -> "WorkflowRecommendationHistory":
        recommendation_ids = {item.recommendation_id for item in self.recommendations}
        if self.recommendations and self.latest_recommendation_id is None:
            raise ValueError("latest_recommendation_id is required when recommendations are present")
        if self.latest_recommendation_id is not None and self.latest_recommendation_id not in recommendation_ids:
            raise ValueError("latest_recommendation_id must match a history entry")
        return self
