from qdrant_client import QdrantClient

# Assuming you've already defined your `client` and uploaded your documents
client = QdrantClient(":memory:")
# Get the size of the collection
# Function to count documents in the collection


def count_documents_in_collection(client, collection_name):
    count = 0
    for _ in client.search(collection_name=collection_name, query_vector=[], limit=1):
        count += 1
    return count


# Example usage
client = QdrantClient(":memory:")  # Initialize your QdrantClient instance

# Assuming 'my_books' is your collection name
collection_name = "my_books"

# Count documents
collection_size = count_documents_in_collection(client, collection_name)
print(f"Number of documents embedded: {collection_size}")
