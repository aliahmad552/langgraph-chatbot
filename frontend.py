import streamlit as st
from backend_langgraph import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage,ToolMessage
import uuid

# ******************************************************************************
#                              Helper Functions
# ******************************************************************************

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

# ******************************************************************************
#                              Streamlit App UI
# ******************************************************************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads() 

add_thread(st.session_state['thread_id'])

# ******************************************************************************
#                                 Sidbar UI
# ******************************************************************************

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

# ******************************************************************************
#                                   Main UI
# ******************************************************************************


for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable':{'thread_id': st.session_state['thread_id']}}

    with st.chat_message("assistant"):
        # Mutable holder to keep ONE status box across tool calls
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Detect tool usage and show/update status
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")

                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …",
                            expanded=True,
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens (hide tool output)
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        # Stream the assistant response live
        ai_message = st.write_stream(ai_only_stream())

        # Finalize tool status (only if a tool was used)
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished",
                state="complete",
                expanded=False,
            )

    # Save assistant message to session history
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
