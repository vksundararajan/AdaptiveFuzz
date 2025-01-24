import ollama

desired_model = "llama3.2"
sample_message = "This is a test message to check the basic functionality of the Ollama model."

try:
  response = ollama.chat(
    model=desired_model,
    messages=[
      {
        "role": "user",
        "content": sample_message,
      },
    ],
  )

  ollama_response = response["message"]["content"]
  print("Response from Ollama:")
  print(ollama_response)

except Exception as e:
  print(f"An error occurred: {e}")
