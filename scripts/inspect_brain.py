import chromadb
from chromadb import PersistentClient

DB_PATH = "../HubermanBotDB"
COLLECTION_NAME = "hubermanbot_chunks"

# Connect to ChromaDB
client = PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Show total chunks
total_chunks = collection.count()
print(f"\n📊 Total chunks in collection: {total_chunks}")

# Get all IDs to check for gaps
all_ids = collection.get(include=[])["ids"]
print(f"\n📋 Total unique IDs: {len(all_ids)}")

# View specific chunks interactively
while True:
    user_input = input("\n🔍 Enter a chunk index to view (or type 'q' to quit): ").strip()
    if user_input.lower() == 'q':
        break
    if not user_input.isdigit():
        print("❌ Please enter a valid number.")
        continue

    idx = int(user_input)
    try:
        # Get all IDs and filter for the ones ending with chunk_{idx}
        all_results = collection.get(include=["documents", "metadatas"])
        matching_ids = [id for id in all_results["ids"] if id.endswith(f"chunk_{idx}")]
        
        if not matching_ids:
            print(f"❌ No content found for chunk {idx}")
            continue
            
        # Get the first matching chunk
        result = collection.get(ids=[matching_ids[0]], include=["documents", "metadatas"])
        doc = result["documents"][0]
        meta = result["metadatas"][0]

        print(f"\n--- Chunk {idx} ---")
        print(f"Title: {meta.get('title', 'N/A')}")
        print(f"Summary: {meta.get('summary', 'N/A')}")
        print(f"Category: {meta.get('category', 'N/A')}")
        print(f"Content: {doc[:1000]}...")
    except Exception as e:
        print(f"❌ Error accessing chunk {idx}: {str(e)}")
        continue
