import os
from together import Together
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TOGETHER_API_KEY")

client = Together(api_key=api_key)

# response = client.chat.completions.create(
#     model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
#     messages=[{"role": "user", "content": "What are some fun things to do in New York?"}],
# )
# print(response.choices[0].message.content)

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "You are an AI assistant specialized in answering technology-related questions."},
        {"role": "user", "content": "Explain how Kubernetes helps manage microservices."}
    ],
    max_tokens=200,
    temperature=0.7,
    top_p=0.7,
    top_k=50,
    repetition_penalty=1,
    stop=["<｜end▁of▁sentence｜>"],
    stream=True
)

for token in response:
    if hasattr(token, 'choices') and token.choices:
        if hasattr(token.choices[0], 'delta') and hasattr(token.choices[0].delta, 'content'):
            print(token.choices[0].delta.content, end='', flush=True)

