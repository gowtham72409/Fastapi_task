import ollama

def generate_answer(user_input):
    response = ollama.chat(
        model="phi3",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant"},
            {"role": "user", "content": user_input}
        ]
    )

    return response['message']['content']