from openai import OpenAI

model = OpenAI(model_name="gpt-4")

result  = model.invoke("Hello, world")
print(result)