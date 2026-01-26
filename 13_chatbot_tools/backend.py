from langgraph.graph import START, StateGraph, END
from typing import TypedDict, Literal, List, Annotated
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langchain.schema.messages import BaseMessage, HumanMessage,AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, Dict
from langchain_core.tools import tool
import os
from langgraph.prebuilt import tools_condition, ToolNode
import requests
import sqlite3
from dotenv import load_dotenv
load_dotenv()


# Tools

search_tool = DuckDuckGoSearchRun(region="en-us")


@tool
def calculator(first_num: float, second_num: float, operation: str) -> Dict:
    """
    Peform a basic arithmatic opeation on two number:
    operations:
     - add
     - sub
     - mul
     - div
    """
    try:
        if operation == 'add':
            result = first_num+second_num
        elif operation == 'sub':
            result = first_num-second_num
        elif operation == 'mul':
            result = first_num*second_num
        elif operation == 'div':
            result = first_num/second_num
        else:
            return {"error": f"Unsupported Operation '{operation}'"}

        return {'first_num': first_num, 'second_num': second_num, 'operation': operation, 'result': result}
    except Exception as e:
        return {'error': str(e)}


@tool
def get_stock_price(symbol: str) -> Dict:
    """
    Fetch latest stock price form a given symbol like AAPL,TSLA,.....
    using APLHA vantage with API key in the URL
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
    response = requests.get(url)
    return response.json()


tools = [get_stock_price, search_tool, calculator]


class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)
# function


def chat_node(state: ChatState):
    """LLM Node that may answer or request a tool call"""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}


tool_node = ToolNode(tools)


# db
conn = sqlite3.connect(database='chatbot.sqlite3', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)
# nodels
graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)
# edges
graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')
graph.add_edge('chat_node', END)

# compile
workflow = graph.compile(checkpointer=checkpointer)
chatbot = workflow
# Get list of thread


def retrive_all_threads():
    all_thread = set()
    for checkpoint in checkpointer.list(None):
        all_thread.add(checkpoint.config.get(
            'configurable', {}).get('thread_id'))
    return list(all_thread)
