import time

from app.semantic_search import semantic_search


TEST_CASES = [
    {
        "question": "How much vacation time do employees get?",
        "expected_document": "employee_policy.txt",
        "expected_chunk": 0
    },
    {
        "question": "How many days can employees work remotely?",
        "expected_document": "employee_policy.txt",
        "expected_chunk": 1
    },
    {
        "question": "When does employee medical coverage begin?",
        "expected_document": "employee_policy.txt",
        "expected_chunk": 2
    },
    {
        "question": "What equipment do employees receive when they start?",
        "expected_document": "employee_policy.txt",
        "expected_chunk": 3
    },
    {
        "question": "Why are COA and BRC not applicable?",
        "expected_document": "COA.pdf",
        "expected_chunk": 0
    },
    {
        "question": "What is the maternity leave policy?",
        "expected_document": None,
        "expected_chunk": None
    }
]


def evaluate():

    correct = 0
    total = len(TEST_CASES)

    total_latency = 0

    print("\nRAG RETRIEVAL EVALUATION")
    print("=" * 70)

    for number, case in enumerate(TEST_CASES, start=1):

        start = time.perf_counter()

        results = semantic_search(
            query=case["question"],
            limit=5
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        total_latency += latency_ms

        print(f"\nTest {number}")
        print(f"Question: {case['question']}")

        # Unsupported question
        if case["expected_document"] is None:

            if not results:
                print("Expected: No relevant document")
                print("Result: No relevant document")
                print("PASS ✅")
                correct += 1

            else:
                chunk, distance = results[0]

                print("Expected: No relevant document")
                print(
                    f"Result: {chunk.document_name}, "
                    f"chunk {chunk.chunk_index}"
                )
                print(
                    f"Distance: {float(distance):.4f}"
                )
                print("FAIL ❌")

        # Supported question
        else:

            if not results:
                print(
                    "Expected:",
                    case["expected_document"],
                    "chunk",
                    case["expected_chunk"]
                )
                print("Result: No result")
                print("FAIL ❌")

            else:
                chunk, distance = results[0]

                matched = (
                    chunk.document_name
                    == case["expected_document"]
                    and
                    chunk.chunk_index
                    == case["expected_chunk"]
                )

                print(
                    "Expected:",
                    case["expected_document"],
                    "chunk",
                    case["expected_chunk"]
                )

                print(
                    "Result:",
                    chunk.document_name,
                    "chunk",
                    chunk.chunk_index
                )

                print(
                    f"Distance: {float(distance):.4f}"
                )

                if matched:
                    print("PASS ✅")
                    correct += 1
                else:
                    print("FAIL ❌")

        print(
            f"Retrieval latency: "
            f"{latency_ms:.2f} ms"
        )

    accuracy = (
        correct / total
    ) * 100

    avg_latency = (
        total_latency / total
    )

    print("\n" + "=" * 70)

    print(
        f"Passed: {correct}/{total}"
    )

    print(
        f"Accuracy: {accuracy:.1f}%"
    )

    print(
        f"Average retrieval latency: "
        f"{avg_latency:.2f} ms"
    )


if __name__ == "__main__":
    evaluate()