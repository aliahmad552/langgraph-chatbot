from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-4.1-mini")

result = model.invoke("Hello, world")
print(result.content)