import os
import sqlite3
import tempfile
from typing import Annotated, Any, Dict, Optional, TypedDict

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
import requests


load_dotenv()


# ============== 1. LLM + embeddings ======
llm = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# ============== 2. PDF Retriever ======
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}


def _get_retriever(thread_id: Optional[str]):
    """Fetch the retiriever for a thread if available"""
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    return None


def ingest_pdf(file_bytes: bytes, thread_id: str, file_name: Optional[str] = None) -> dict:
    """Builds A FASISS Vector store for save embed documents, and store it to related thread id
    Returns: A Summary dict that can be surfaced in the UI
    """
    if not file_name:
        raise ValueError("No bytes received from ingestion.")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name
    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, seprators=['\n\n', '\n', ''])
        chunks = splitter.split_documents(docs)
        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={'k': 4})
        _THREAD_RETRIEVERS[thread_id] = retriever
        _THREAD_METADATA[thread_id] = {
            'filename': file_name or os.path.basename(temp_path),
            'documents': len(docs),
            'chunks': len(chunks)
        }
        return {
            'filename': file_name or os.path.basename(temp_path),
            'documents': len(docs),
            'chunks': len(chunks)
        }
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


#  ================= 4. Tools =======
search_tool = DuckDuckGoSearchRun()


@tool
def calculator(first_num: float, second_number: float, operation: str) -> dict:
    """
    Perform as basic arithmatic opeation,

    :param first_num: Description
    :type first_num: float
    :param second_number: Description
    :type second_number: float
    :param operation: Description
    :type operation: str
    :return: Description
    :rtype: dict[Any, Any]
    """
    try:
        result = None
        if operation == 'add':
            result = first_num+second_number
        elif operation == 'sub':
            result = first_num-second_number
        elif operation == 'mul':
            result = first_num*second_number
        elif operation == 'div':
            if second_number == 0:
                return {'error': "Division by zero is not allowed"}
            result = first_num/second_number
        else:
            return {"error": "Upsupported opeation  '{operation}'"}

        return {
            'first_num': first_num,
            'second_number': second_number,
            'operation': operation,
            'result': result
        }
    except Exception as e:
        return {'error': str(e)}
