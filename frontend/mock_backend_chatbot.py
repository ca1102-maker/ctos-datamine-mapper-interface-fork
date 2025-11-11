@app.post("/chat")
async def chat_with_gpt(request: Request):
    body = await request.json()
    user_message = body.get("message", "")

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    try:
        print("Received message:", user_message)

        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful biomedical assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        reply = completion.choices[0].message["content"]
        print("GPT reply:", reply)
        return JSONResponse({"reply": reply})

    except Exception as e:
        import traceback
        traceback.print_exc()  # 👈 this prints the real error
        return JSONResponse({"error": str(e)}, status_code=500)
