"""What each CrewAI task must return. Every model answer is validated against one of these (output_pydantic),
and the same JSON schema is handed to Claude (--json-schema), so a malformed answer never reaches the next task."""
from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Shortlist(Contract):
    listing_ids: list[str]
    note: str


class Plan(Contract):
    checks: list[str]
    note: str


class Choice(Contract):
    listing_id: str
    reason: str


class Decision(Contract):
    action: str          # trigger | ignore
    reason: str
