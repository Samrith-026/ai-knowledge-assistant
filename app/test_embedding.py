from app.embeddings import create_embedding


text = "Employees receive 15 days of PTO each year."

embedding = create_embedding(text)

print("Original text:")
print(text)

print("\nEmbedding length:")
print(len(embedding))

print("\nFirst 5 numbers:")
print(embedding[:5])