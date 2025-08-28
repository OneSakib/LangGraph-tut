from langgraph.graph import START, StateGraph, END
from typing import TypedDict, Literal, List, Annotated
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langchain.schema.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from dotenv import load_dotenv
load_dotenv()


class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o")
# function


def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {'messages': [response]}


# db
conn = sqlite3.connect(database='chatbot.sqlite3', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)
# nodels
graph.add_node('chat_node', chat_node)
# edges
graph.add_edge(START, 'chat_node')
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
