import streamlit as st
from main import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "Multi-Agent Software Team (LangGraph)"
icon = "🤖"

def generate_message(user_input):
    response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]

    st.session_state.conversation.append({
        "user": user_input,
        "weather": response["messages"][-4].content,
        "hotels": response["messages"][-3].content,
        "restaurants": response["messages"][-2].content,
        "transportation": response["messages"][-1].content,
    })

    # Iterate over the conversation history
    for entry in st.session_state.conversation:
        messages.chat_message("user", avatar = "icons/user.svg").write(entry["user"])
        messages.chat_message("weather", avatar = "icons/analyst.svg").write(entry["weather"])
        messages.chat_message("hotels", avatar = "icons/architect.svg").write(entry["hotels"])
        messages.chat_message("restaurants", avatar = "icons/designer.svg").write(entry["restaurants"])
        messages.chat_message("transportation", avatar = "icons/developer.svg").write(entry["transportation"])

# Session : Initialize conversation history
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Streamlit app
st.set_page_config(page_title = title, page_icon = icon, layout = "wide")
st.header(title)


# Create a container for the chat messages
messages = st.container(border = True, height = height)

# Chatbot UI
if prompt := st.chat_input("Enter a message", key="prompt"):
    generate_message(prompt)

