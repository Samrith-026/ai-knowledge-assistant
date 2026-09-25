from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        description="Question to ask the knowledge base"
    )


class SourceItem(BaseModel):
    document_name: str
    chunk_index: int
    content: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]

class UploadResponse(BaseModel):
    filename: str
    chunks_created: int
    message: str