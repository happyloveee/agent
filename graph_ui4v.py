import streamlit as st
from main2v import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "Multi-Agent Software Team (LangGraph)"
icon = "🤖"

# 세션 초기화: 두 파일 모두에서 대화 기록과 세션 저장소를 사용
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "store" not in st.session_state:
    st.session_state.store = {}

def generate_message(user_input):
    # 사용자가 입력한 메시지를 즉시 출력 (대화 기록에 추가하기 전에)
    st.chat_message("user", avatar="icons/user.svg").write(user_input)
    
    # state 초기화
    state = {
        "messages": [HumanMessage(content=user_input)],
        "selected_nodes": [],
        "outputs": {}
    }
    response = graph.invoke(state)
    outputs = response.get("outputs", {})

    # 대화 기록에 사용자 메시지와 결과 추가
    conversation_entry = {"user": user_input}
    conversation_entry.update(outputs)
    st.session_state.conversation.append(conversation_entry)

    # AI의 응답도 출력 (전체 대화 기록 갱신)
    for entry in st.session_state.conversation:
        if "weather" in entry:
            st.chat_message("weather", avatar="icons/analyst.svg").write(entry["weather"])
        if "hotels" in entry:
            st.chat_message("hotels", avatar="icons/architect.svg").write(entry["hotels"])
        if "restaurants" in entry:
            st.chat_message("restaurants", avatar="icons/designer.svg").write(entry["restaurants"])
        if "transportation" in entry:
            st.chat_message("transportation", avatar="icons/developer.svg").write(entry["transportation"])
        if "tavily" in entry:
            st.chat_message("tavily", avatar="icons/tester.svg").write(
                "\n".join([f"{domain}: {result}" for domain, result in entry["tavily"].items()])
            )

# Streamlit 앱 설정
st.set_page_config(page_title=title, page_icon=icon, layout="wide")
st.header(title)

# 좌측 사이드바: 세션 ID 입력 및 대화 기록 초기화 버튼 추가
with st.sidebar:
    session_id = st.text_input("Session ID", value="abc123")
    if st.button("대화 기록 초기화"):
        st.session_state.conversation = []
        st.session_state.store = {}
        st.experimental_rerun()

# 채팅 메시지 컨테이너 생성
messages = st.container()

# Chatbot UI: 사용자가 메시지를 입력하면 generate_message() 호출
if prompt := st.chat_input("메세지를 입력해주세요!", key="prompt"):
    generate_message(prompt)
