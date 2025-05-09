from zyphra import ZyphraClient
import os

zyphra_api_key = os.getenv('ZYPHRA_API_KEY')

client = ZyphraClient(api_key=zyphra_api_key)

output_path = client.audio.speech.create(
    text="My name is Dr. AndrewHuberman.",
    voice_name="Huberman",
    speaking_rate=15,
    output_path="output.webm"
)

print(f"Output path: {output_path}")