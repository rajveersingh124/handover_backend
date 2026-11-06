
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

api_key = os.getenv("APINEX_API_KEY")

if not api_key:
    print("API Key not found! Check your .env file.")

else:
    try:
        print("Connecting to APInex...", flush=True)

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.apinex.bond/v1",
            timeout=20.0,
            max_retries=0
        )

        print("Sending request to Gemini AI...", flush=True)

        response = client.chat.completions.create(
            model="free/gemini-3.8-flash",
            messages=[
                {
                    "role": "user",
                    "content": "Explain HandoverHub AI in simple English."
                }
            ],
            max_tokens=150
        )

        print("\n===== AI RESPONSE =====")

        print(response.choices[0].message.content)

        print("\nAI connection successful!")

    except Exception as error:
        print("\nAPI ERROR:")
        print(type(error).__name__, str(error))
