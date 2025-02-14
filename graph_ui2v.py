import streamlit as st
from main2v import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "Multi-Agent Software Team (LangGraph)"
icon = "🤖"

def generate_message(user_input):
    # 동적 분기를 사용하는 경우, state에 selected_nodes와 outputs도 포함합니다.
    state = {
        "messages": [HumanMessage(content=user_input)],
        "selected_nodes": [],
        "outputs": {}
    }
    response = graph.invoke(state)
    outputs = response.get("outputs", {})

    # 대화 기록에 사용자 메시지와 동적으로 실행된 노드 결과를 추가합니다.
    conversation_entry = {"user": user_input}
    conversation_entry.update(outputs)
    st.session_state.conversation.append(conversation_entry)

    # 대화 기록을 순회하며, 존재하는 각 노드의 결과만 출력합니다.
    for entry in st.session_state.conversation:
        messages.chat_message("user", avatar="icons/user.svg").write(entry["user"])
        if "weather" in entry:
            messages.chat_message("weather", avatar="icons/analyst.svg").write(entry["weather"])
        if "hotels" in entry:
            messages.chat_message("hotels", avatar="icons/architect.svg").write(entry["hotels"])
        if "restaurants" in entry:
            messages.chat_message("restaurants", avatar="icons/designer.svg").write(entry["restaurants"])
        if "transportation" in entry:
            messages.chat_message("transportation", avatar="icons/developer.svg").write(entry["transportation"])
        if "tavily" in entry:
            messages.chat_message("tavily", avatar="icons/tester.svg").write("최신 정보 보충: " + entry["tavily"])

# Session : 대화 기록 초기화
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Streamlit app 설정
st.set_page_config(page_title=title, page_icon=icon, layout="wide")
st.header(title)

# 채팅 메시지 컨테이너 생성
messages = st.container()

# Chatbot UI: 사용자가 메시지를 입력하면 generate_message() 호출
if prompt := st.chat_input("Enter a message", key="prompt"):
    generate_message(prompt)
