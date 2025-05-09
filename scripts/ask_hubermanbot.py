import os
import json
from openai import OpenAI
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from zyphra import ZyphraClient

# Get API keys from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
zyphra_api_key = os.getenv('ZYPHRA_API_KEY')

if not openai_api_key or not zyphra_api_key:
    raise ValueError("Please set OPENAI_API_KEY and ZYPHRA_API_KEY environment variables")

# Initialize clients
client = OpenAI(api_key=openai_api_key)
zoros_client = ZyphraClient(api_key=zyphra_api_key)

# Directory setup
db_path = "../HubermanBotDB"

# Initialize Chroma Persistent Client
chroma_client = PersistentClient(path=db_path)
collection = chroma_client.get_or_create_collection(name="hubermanbot_chunks")

# Embedding function
def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# Ask function
def ask_hubermanbot(question):
    # Embed the user's question
    question_embedding = get_embedding(question)

    # Search the collection for top matches
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=int(input("How many results would you like to see? ")),
        include=["documents", "metadatas"]
    )

    # Build context from retrieved documents
    context_chunks = [doc for doc in results["documents"][0]]
    context_text = "\n\n".join(context_chunks)

    print("CONTEXT CHUNKS: ", context_text + "\n\n Answer Prompt: ")

    # Build prompt for GPT-4o
    system_prompt = (
        "Speak in a detailed, science-backed style, similar to the speaking manner in the context providid. You are the host of the Huberman Lab Podcast, Andrew Huberman. Be clear, encouraging, conversational, and cite specific mechanisms where possible. Provide step-by-step, science-based protocols if asked. Your protols should be 3 questions long max. Start with the action protocol, then ask if the user would like to know more about the science behind any of the sections."
    )

    user_prompt = (
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Be conversational and talk in a similar manner to Andrew Huberman. If you don't see the answer in the context, respond with 'Sorry, I dont have context on that.'"
    )

    # Query GPT-4o
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # Return the GPT-generated answer
    return response.choices[0].message.content

# send answer to Zonos API key and generate audio file respon
def generate_audio_response(answer):
    output_path = zoros_client.audio.speech.create(
        text=answer,
        voice_name="Huberman",
        speaking_rate=15,
        output_path="output.webm"
    )

# Command line interface
if __name__ == "__main__":
    print("✅ HubermanBot is ready. Ask your question!")
    while True:
        user_question = input("\nYou: ")
        if user_question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        answer = ask_hubermanbot(user_question)
        print(answer)
        generate_audio_response("My name is Huberman.")