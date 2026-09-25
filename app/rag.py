import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.exceptions import RAGServiceError
from app.semantic_search import semantic_search


load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL")


def answer_question(question: str):

    logger.info(
        "Processing question: %s",
        question
    )

    try:

        results = semantic_search(
            query=question,
            limit=5
        )

        logger.info(
            "Retrieved %d relevant chunks",
            len(results)
        )

        if not results:

            logger.warning(
                "No sufficiently relevant context found"
            )

            return {
                "answer": (
                    "I don't have enough information "
                    "in the provided documents."
                ),
                "sources": []
            }

        context_parts = []
        sources = []

        for index, (chunk, distance) in enumerate(
            results,
            start=1
        ):

            logger.info(
                "Source %d: document=%s "
                "chunk=%d distance=%.4f",
                index,
                chunk.document_name,
                chunk.chunk_index,
                float(distance)
            )

            context_parts.append(
                f"[Source {index}]\n"
                f"Document: {chunk.document_name}\n"
                f"Content: {chunk.content}"
            )

            sources.append(
                {
                    "document_name": chunk.document_name,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "distance": float(distance)
                }
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
Answer the question using only the provided context.

When you use information from a source, cite it using the source number,
for example: [Source 1].

If the answer is not supported by the context, say:
"I don't have enough information in the provided documents."

Context:
{context}

Question:
{question}
"""

        logger.info(
            "Calling LLM with %d relevant sources",
            len(results)
        )

        response = client.responses.create(
            model=MODEL,
            input=prompt
        )

        logger.info(
            "LLM response generated successfully"
        )

        return {
            "answer": response.output_text,
            "sources": sources
        }

    except Exception as exc:

        logger.exception(
            "RAG request failed"
        )

        raise RAGServiceError(
            "Unable to complete the RAG request"
        ) from exc


if __name__ == "__main__":

    question = "How much vacation time do employees get?"

    result = answer_question(question)

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:
        print(source)