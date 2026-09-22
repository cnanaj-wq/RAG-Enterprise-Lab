from pydantic import BaseModel, Field


class ExpectedAnswer(BaseModel):
    question_id: str
    category: str
    question: str
    expected_answer: object
    source_document_ids: list[str] = Field(default_factory=list)
