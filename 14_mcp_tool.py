from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
import asyncio
load_dotenv()

llm = ChatOpenAI(model="gpt-5")


def calculator(first_number: float, second_number: float, opeation: str) -> dict:
    """
    Perform a basic arithmatic opeation
    it accept two peramater first_number and second_number and opeation. like (add,sub,mul,div etc.)
    """
    result = 0
    if opeation == 'add':
        result = first_number+second_number
    elif opeation == 'sub':
        result = first_number-second_number
    elif opeation == 'mul':
        result = first_number*second_number
    elif opeation == 'div':
        result = first_number/second_number
    else:
        return {'first_number': first_number, 'second_number': second_number, 'opeation': opeation, 'error': "Invalid Opeation, plesae choose correct opeation"}
    return {'first_number': first_number, 'second_number': second_number, 'opeation': opeation, 'result': result}


tools = [calculator]
llm_with_tool = llm.bind_tools(tools)
# State


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_graph():
    async def chat_node(state: ChatState):
        messages = state['messages']
        response = await llm_with_tool.ainvoke(messages)
        return {'messages': [response]}

    tool_node = ToolNode(tools)
    graph = StateGraph(ChatState)

    graph.add_node('chat_node', chat_node)
    graph.add_node('tools', tool_node)

    graph.add_edge(START, 'chat_node')
    graph.add_conditional_edges('chat_node', tools_condition)
    graph.add_edge('tools', 'chat_node')

    chatbot = graph.compile()
    return chatbot


async def main():
    chatbot = build_graph()
    # Result
    result = await chatbot.ainvoke({'messages': [HumanMessage(content="Find the modulas of 34.")]})
    print("Result:", result)
    return

if __name__ == '__main__':
    asyncio.run(main())
