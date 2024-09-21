from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import sqlite3
import google.generativeai as genai
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the sentence transformer model
encoder = SentenceTransformer("all-MiniLM-L6-v2")


def read_from_sqlite(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT link, message_text FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data


# Set up paths and names
db_path = 'uybozor.db'
table_name = 'scraped_data'
collection_name = "uybozor_data"
qdrant_storage_path = "./qdrant_storage"

# Create QdrantClient with persistent storage
client = QdrantClient(path=qdrant_storage_path)

# Check if the collection already exists
collections = client.get_collections()
collection_exists = any(
    collection.name == collection_name for collection in collections.collections)

if not collection_exists:
    print(f"Creating new collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=encoder.get_sentence_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
    )

    # Read data from SQLite and upload to Qdrant
    data = read_from_sqlite(db_path, table_name)

    client.upload_points(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=idx,
                vector=encoder.encode(message_text).tolist(),
                payload={"link": link, "message_text": message_text}
            )
            for idx, (link, message_text) in enumerate(data[:100], start=1)
        ],
    )
    print("Data uploaded successfully.")
else:
    print(f"Collection {collection_name} already exists. Using existing data.")


def retrieve_and_generate(query, top_k=15):
    # Retrieve relevant documents
    hits = client.search(
        collection_name=collection_name,
        query_vector=encoder.encode(query).tolist(),
        limit=top_k,
    )

    for hit in hits:
        print(hit)

    # Prepare context from retrieved documents
    context = "\n".join([hit.payload['message_text'] for hit in hits])

    # Prepare the prompt
    prompt = f"""rewrite and improve the context and remove unnecessary things like youtube or instagram or telegram and send it to user
    
    Context: {context}
    
    Query: {query}
    
    Response:"""

    # Generate response using Gemini API
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    return response.text, hits


# Example usage
query = "Chilonzorda 2 xonali kvartira"
generated_response, hits = retrieve_and_generate(query)

print(f"\nQuery: '{query}'")
print(f"\nGenerated Response:\n{generated_response}")

print("\nRetrieved Documents:")
for hit in hits:
    print(f"Score: {hit.score}")
    print(f"Link: {hit.payload['link']}")
    print(f"Message: {hit.payload['message_text'][:100]}...")
    print()
