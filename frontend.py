import streamlit as st
from backend_langgraph import chatbot
from langchain_core.messages import HumanMessage
import uuid

# ----------------------------------------------------------------------
#                         Streamlit Utility Func
# ----------------------------------------------------------------------

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config ={'configurable': {'thread_id':thread_id}}).values.get("messages", [])

# ----------------------------------------------------------------------
# -------------------------- Session State ------------------------------
# ----------------------------------------------------------------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = [] 

add_thread(st.session_state['thread_id'])

# ----------------------------------------------------------------------
#                         Sidbar UI
# ----------------------------------------------------------------------

st.sidebar.title('Mini Chat AI')

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for message in messages:
            role = 'user' if isinstance(message, HumanMessage) else 'assistant'
            temp_messages.append({
                'role':role,
                'content':message.content
            })
        st.session_state['message_history'] = temp_messages

# ----------------------------------------------------------------------
#                              Main UI
# ----------------------------------------------------------------------


for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable':{'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        ai_response = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content = user_input)]},
                config = CONFIG,
                stream_mode = 'messages'
            )
        )
    st.session_state['message_history'].append({'role':'assistant','content': ai_response})
