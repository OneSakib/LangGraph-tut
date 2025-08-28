from langgraph.graph import START, StateGraph, END
from typing import TypedDict, Literal, List, Annotated
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langchain.schema.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables.config import RunnableConfig
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


checkpointer = InMemorySaver()
graph = StateGraph(ChatState)
# nodels
graph.add_node('chat_node', chat_node)
# edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

# compile
workflow = graph.compile(checkpointer=checkpointer)
chatbot = workflow
# thread_id = 'dnfgjkhdfjkgfdk455656'
# while True:
#     user_input = input('Type here: ')
#     print("User: ", user_input)
#     if user_input.strip().lower() in ['exit', 'quit', 'bye']:
#         break
#     config: RunnableConfig = {'configurable': {'thread_id': thread_id}}
#     # response = workflow.invoke(
#     #     {'messages': [HumanMessage(content=user_input)]}, config=config)
#     # print('Ai:', response['messages'][-1].content)
#     response = workflow.stream(
#         {'messages': [HumanMessage(content=user_input)]}, config=config, stream_mode="messages")
#     print("AI: ", end="\b")
#     for message_chunk, meta in response:
#         if message_chunk.content:
#             print(message_chunk.content, end="", flush=True)
#     print("\n")
