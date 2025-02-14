import streamlit as st
import uuid
from datetime import datetime, date
from main2v import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "Multi-Agent Software Team (LangGraph)"
icon = "🤖"

# 세션 초기화: 대화 기록, 세션 저장소, 대화 히스토리, session_id
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "store" not in st.session_state:
    st.session_state.store = {}
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = {}  # { "YYYY-MM-DD": [대화기록, ...] }
if "session_id" not in st.session_state:
    st.session_state.session_id = "abc123"

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

    # 전체 대화 기록 갱신하여 AI 응답 출력
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

# 좌측 사이드바: Session ID 입력, 대화 기록 초기화, 새 대화하기 버튼 추가
with st.sidebar:
    # session_id를 세션 상태에서 가져와서 텍스트 입력창에 기본값으로 사용
    st.text_input("Session ID", value=st.session_state.session_id, key="session_id_input")
    
    if st.button("대화 기록 초기화"):
        st.session_state.conversation = []
        st.session_state.store = {}
        st.rerun()
    
    if st.button("새 대화하기"):
        # 현재 대화가 존재하면 날짜별로 보관 (첫 질문 10글자를 제목으로)
        if st.session_state.conversation:
            first_question = st.session_state.conversation[0].get("user", "")
            title_conv = first_question[:10] if first_question else "Untitled"
            conversation_record = {
                "session_id": st.session_state.session_id,
                "title": title_conv,
                "conversation": st.session_state.conversation,
                "timestamp": datetime.now().isoformat()
            }
            today_str = date.today().isoformat()
            if today_str not in st.session_state.conversation_history:
                st.session_state.conversation_history[today_str] = []
            st.session_state.conversation_history[today_str].append(conversation_record)
        
        # 새 대화를 위해 기존 대화 및 저장소 초기화
        st.session_state.conversation = []
        st.session_state.store = {}
        # 새로운 session id 생성 (예: UUID의 앞 8자리)
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()

# 채팅 메시지 컨테이너 생성
messages = st.container()

# Chatbot UI: 사용자가 메시지를 입력하면 generate_message() 호출
if prompt := st.chat_input("메세지를 입력해주세요!", key="prompt"):
    generate_message(prompt)
