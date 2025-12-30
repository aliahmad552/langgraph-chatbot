from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langsmith import traceable
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
import sqlite3

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

import requests

# ****************************** Load environment variables **************

load_dotenv()

# ****************************** Chat State ******************************

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

# ****************************** Language Model ***************************

model1 = ChatOpenAI(model='gpt-4o-mini')

# **************************** TOOLS *************************************

# Tools
search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calculator(first_num: float, second_num: float, operation: str) -> float:
    """Performs basic arithmetic operations."""
    if operation == 'add':
        return first_num + second_num
    elif operation == 'subtract':
        return first_num - second_num
    elif operation == 'multiply':
        return first_num * second_num
    elif operation == 'divide':
        if second_num == 0:
            return "Error: Division by zero"
        return first_num / second_num
    else:
        return "Error: Unsupported operation"
    
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g, 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """
    URL = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=5H641FJLGGY0JCG1'
    response = requests.get(URL)
    return response.json()

# ****************************** LLM With Tools ***************************

tools = [search_tool, calculator, get_stock_price]

llm_with_tools = model1.bind_tools(tools)

# ****************************** Graph Nodes ******************************

@traceable(name="chat_node_func", tags=["chatbot", "langgraph"])
def chat_node(state: ChatState):
    """LLM node that may answer or request tool call."""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

tool_node = ToolNode(tools) # Execute tool calls

# ****************************** State Graph ******************************

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools','chat_node')

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn = conn)
chatbot = graph.compile(checkpointer = checkpointer)

# ****************************** Retrieve all threads ************************

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)
 