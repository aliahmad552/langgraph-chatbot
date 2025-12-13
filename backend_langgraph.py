from langgraph.graph import StateGraph, START, END
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated

# ------------------------------ load env --------------------------------

load_dotenv()

# ------------------------------ chat state ------------------------------

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

# ------------------------------ chat model ------------------------------

llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation"
    )
model = ChatHuggingFace(llm=llm)

# ------------------------------ chat node  ------------------------------

def chat_node(state: ChatState):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages': response}

# ------------------------------ graph defination -------------------------

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

checkpointer = InMemorySaver()
chatbot = graph.compile(checkpointer = checkpointer)
