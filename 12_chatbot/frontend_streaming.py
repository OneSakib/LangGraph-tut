import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

# st.session_state -> dict ->
CONFIG: RunnableConfig = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

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
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            chunk_message.content for chunk_message, meta_data in chatbot.stream({'messages': [HumanMessage(
                content=user_input)]}, config=CONFIG, stream_mode="messages")
        )
    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': ai_message})
