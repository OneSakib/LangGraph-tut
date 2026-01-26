import streamlit as st
from backend import chatbot, retrive_all_threads
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from uuid import uuid4


# -------------- uitlity function

def generate_thread_id() -> str:
    return str(uuid4())


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_threads(thread_id)


def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversations(thread_id):
    config: RunnableConfig = {'configurable': {'thread_id': thread_id}}
    return chatbot.get_state(config=config).values.get('messages', {})

# -------------- uitlity function


# Sesssion Setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrive_all_threads()

add_threads(st.session_state['thread_id'])

# Sesssion Setup

# Sidebar UI
st.sidebar.title("LangGraph Chatbot")

new_chat_button = st.sidebar.button("New Chat")
if new_chat_button:
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        messages = load_conversations(thread_id)
        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                temp_messages.append({
                    'role': 'user',
                    'content': message.content
                })
            else:
                temp_messages.append({
                    'role': 'assistant',
                    'content': message.content
                })
        st.session_state['message_history'] = temp_messages
# Sidebar UI


# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')
if user_input:
    # first add the message to message_history
    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    # st.session_state -> dict ->
    CONFIG: RunnableConfig = {'configurable': {
        'thread_id': st.session_state['thread_id']}}
    # with st.chat_message('assistant'):
    #     ai_message = st.write_stream(
    #         chunk_message.content for chunk_message, meta_data in chatbot.stream({'messages': [HumanMessage(
    #             content=user_input)]}, config=CONFIG, stream_mode="messages")
    #     )
    # st.session_state['message_history'].append(
    #     {'role': 'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        def ai_only_stream():
            for chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                if isinstance(chunk, AIMessage):
                    yield chunk.content
        ai_message = st.write_stream(ai_only_stream())
    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': ai_message})
