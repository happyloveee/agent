import streamlit as st
import uuid
from datetime import datetime, date
from main4v import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "🤖 Multi-Agent Software "
icon = "🤖"

# 세션 초기화: 현재 대화, 저장소, 날짜별 대화 히스토리, session_id, 이전 대화 불러오기 플래그
if "conversation" not in st.session_state:
    st.session_state.conversation = []  # 각 항목은 {"user": <메시지>, "weather": <응답>, ...}
if "store" not in st.session_state:
    st.session_state.store = {}
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = {}  # { "YYYY-MM-DD": [대화 기록, ...] }
if "session_id" not in st.session_state:
    st.session_state.session_id = "abc123"
if "conversation_loaded_from_history" not in st.session_state:
    st.session_state.conversation_loaded_from_history = False


def render_conversation():
    """페이지 로드시 전체 대화 내역 렌더링 (사용자 메시지와 에이전트 메시지 모두 출력)"""
    for entry in st.session_state.conversation:
        if "user" in entry:
            st.chat_message("user", avatar="icons/user.svg").write(entry["user"])
        if "weather" in entry:
            st.chat_message("weather", avatar="icons/weather.svg").write(entry["weather"])
        if "hotels" in entry:
            st.chat_message("hotels", avatar="icons/hotel.svg").write(entry["hotels"])
        if "restaurants" in entry:
            st.chat_message("restaurants", avatar="icons/restaurant.svg").write(entry["restaurants"])
        if "transportation" in entry:
            st.chat_message("transportation", avatar="icons/transportation.svg").write(entry["transportation"])
        if "etc" in entry:
            st.chat_message("etc", avatar="icons/no.svg").write(entry["etc"])

def render_new_message(entry):
    """새 메시지 1개만 렌더링 (중복 출력 방지용)"""
    if "user" in entry:
        st.chat_message("user", avatar="icons/user.svg").write(entry["user"])
    if "weather" in entry:
        st.chat_message("weather", avatar="icons/weather.svg").write(entry["weather"])
    if "hotels" in entry:
        st.chat_message("hotels", avatar="icons/hotel.svg").write(entry["hotels"])
    if "restaurants" in entry:
        st.chat_message("restaurants", avatar="icons/restaurant.svg").write(entry["restaurants"])
    if "transportation" in entry:
        st.chat_message("transportation", avatar="icons/transportation.svg").write(entry["transportation"])
    if "etc" in entry:
        st.chat_message("etc", avatar="icons/no.svg").write(entry["etc"])

def generate_message(user_input):
    # 1. 사용자 메시지를 세션에 저장하고 즉시 출력
    conversation_entry = {"user": user_input}
    st.session_state.conversation.append(conversation_entry)
    st.chat_message("user", avatar="icons/user.svg").write(user_input)
    
    # 2. 답변을 위한 플레이스홀더 생성 (즉시 보여줌)
    placeholder = st.empty()
    placeholder.markdown("🤖 답변을 기다리는 중...")
    
    # 3. 백엔드 호출 및 응답 처리
    state = {
        "messages": [HumanMessage(content=user_input)],
        "selected_nodes": [],
        "outputs": {}
    }
    response = graph.invoke(state)
    outputs = response.get("outputs", {})
    
    # 세션 대화 기록 업데이트
    conversation_entry.update(outputs)
    
    # 플레이스홀더를 비우고, 에이전트 메시지 출력
    placeholder.empty()  # 임시 메시지 제거
    
    if "weather" in outputs:
        st.chat_message("weather", avatar="icons/weather.svg").write(outputs["weather"])
    if "hotels" in outputs:
        st.chat_message("hotels", avatar="icons/hotel.svg").write(outputs["hotels"])
    if "restaurants" in outputs:
        st.chat_message("restaurants", avatar="icons/restaurant.svg").write(outputs["restaurants"])
    if "transportation" in outputs:
        st.chat_message("transportation", avatar="icons/transportation.svg").write(outputs["transportation"])
    if "etc" in outputs:
        st.chat_message("etc", avatar="icons/no.svg").write(outputs["etc"])

# 페이지 설정
st.set_page_config(page_title=title, page_icon=icon, layout="wide")
st.header(title)

# 사이드바: Session ID, 대화 기록 초기화, 새 대화하기, 이전 대화 불러오기
with st.sidebar:
    st.text_input("Session ID", value=st.session_state.session_id, key="session_id_input")
    
    # 대화 기록 초기화: 불러온 대화가 있다면 history에서 삭제 후 현재 대화 클리어
    if st.button("대화 기록 초기화"):
        if st.session_state.conversation_loaded_from_history:
            current_session_id = st.session_state.session_id
            for date_key in list(st.session_state.conversation_history.keys()):
                conv_list = st.session_state.conversation_history[date_key]
                new_conv_list = [conv for conv in conv_list if conv["session_id"] != current_session_id]
                if new_conv_list:
                    st.session_state.conversation_history[date_key] = new_conv_list
                else:
                    del st.session_state.conversation_history[date_key]
        st.session_state.conversation = []
        st.session_state.store = {}
        st.session_state.conversation_loaded_from_history = False
        st.rerun()
    
    # 새 대화하기: (현재 대화가 새로 작성된 경우만) 기록 저장 후, 클리어하고 새 session_id 부여
    if st.button("새 대화하기"):
        if st.session_state.conversation and not st.session_state.conversation_loaded_from_history:
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
        st.session_state.conversation = []
        st.session_state.store = {}
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.conversation_loaded_from_history = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 이전 대화")
    if st.session_state.conversation_history:
        for date_key in sorted(st.session_state.conversation_history.keys(), reverse=True):
            st.markdown(f"#### {date_key}")
            for idx, conv in enumerate(st.session_state.conversation_history[date_key]):
                conv_title = conv["title"]
                conv_time = datetime.fromisoformat(conv["timestamp"]).strftime("%H:%M:%S")
                if st.button(f"{conv_title} ({conv_time})", key=f"{date_key}_{idx}"):
                    st.session_state.conversation = conv["conversation"]
                    st.session_state.session_id = conv["session_id"]
                    st.session_state.conversation_loaded_from_history = True
                    st.rerun()
    else:
        st.write("저장된 대화가 없습니다.")

# 페이지 로드시 기존 대화 내역 렌더링 (초기 로딩 시 한 번만)
if st.session_state.conversation:
    render_conversation()

# 사용자 입력창: 새 메시지 입력 시 generate_message() 호출
if prompt := st.chat_input("메세지를 입력해주세요!", key="prompt"):
    generate_message(prompt)


