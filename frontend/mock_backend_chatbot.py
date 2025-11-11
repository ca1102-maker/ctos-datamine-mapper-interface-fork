# mock_backend_chatbot.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv

# === 1️⃣ Load environment variables ===
load_dotenv()  # reads .env file in same folder
openai.api_key = os.getenv("OPENAI_API_KEY")

# === 2️⃣ Initialize FastAPI app ===
app = FastAPI()

# === 3️⃣ Chat endpoint ===
@app.post("/chat")
async def chat_with_gpt(request: Request):
    """Receive a message from frontend and return ChatGPT response."""
    body = await request.json()
    user_message = body.get("message", "")

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    try:
        # 4️⃣ Send request to OpenAI
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful biomedical assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        # 5️⃣ Extract reply
        reply = completion.choices[0].message["content"]
        return JSONResponse({"reply": reply})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# === 6️⃣ Run server directly (for local dev) ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
