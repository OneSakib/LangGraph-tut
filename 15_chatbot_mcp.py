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
from langchain_mcp_adapters.client import MultiServerMCPClient
load_dotenv()

llm = ChatOpenAI(model="gpt-5")

# ================== CONNSECT MCP CLIENT TO SERVER =================
client = MultiServerMCPClient({  # type: ignore[arg-type]
    "calculator": {
        "transport": "stdio",
        "command": "python",
        "args": ["mcp_servers/main.py"]
    },
    "test-calculator": {
        "transport": "http",
        "url": "https://test-calculator.fastmcp.app/mcp"
    }
})
# ================== CONNSECT MCP CLIENT TO SERVER =================


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def build_graph():
    tools = await client.get_tools()
    llm_with_tool = llm.bind_tools(tools)

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
    chatbot = await build_graph()
    # Result
    result = await chatbot.ainvoke({'messages': [HumanMessage(content="Generata a random number, rannge shold 1000 to 5000")]})
    print("Result:", result['messages'][-1].content)
    return

if __name__ == '__main__':
    asyncio.run(main())
