"""
다른 거는 잘 되나 현재 기존 input 이 사라지고, 그리고 중복 답변이 나옴옴
"""


import streamlit as st
import uuid
from datetime import datetime, date
from main4v import graph
from langchain_core.messages import HumanMessage, AIMessage

# Constants
height = 600
title = "Multi-Agent Software Team (LangGraph)"
icon = "🤖"

# 세션 초기화: 현재 대화, 기타 저장소, 날짜별 대화 히스토리, session_id, 이전 대화 불러오기 여부 플래그
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "store" not in st.session_state:
    st.session_state.store = {}
if "conversation_history" not in st.session_state:
    # { "YYYY-MM-DD": [대화 기록, ...] }
    st.session_state.conversation_history = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = "abc123"
if "conversation_loaded_from_history" not in st.session_state:
    st.session_state.conversation_loaded_from_history = False

def render_conversation():
    """메인 영역에 현재 대화 내역을 렌더링"""
    if st.session_state.conversation:
        for entry in st.session_state.conversation:
            # 각 에이전트의 응답이 있다면 출력
            if "weather" in entry:
                st.chat_message("weather", avatar="icons/analyst.svg").write(entry["weather"])
            if "hotels" in entry:
                st.chat_message("hotels", avatar="icons/architect.svg").write(entry["hotels"])
            if "restaurants" in entry:
                st.chat_message("restaurants", avatar="icons/designer.svg").write(entry["restaurants"])
            if "transportation" in entry:
                st.chat_message("transportation", avatar="icons/developer.svg").write(entry["transportation"])
            if "etc" in entry:
                st.chat_message("etc", avatar="icons/summary.svg").write(entry["etc"])

def generate_message(user_input):
    # 입력한 메시지를 즉시 출력
    st.chat_message("user", avatar="icons/user.svg").write(user_input)
    
    # LangGraph에 전달할 state 생성
    state = {
        "messages": [HumanMessage(content=user_input)],
        "selected_nodes": [],
        "outputs": {}
    }
    response = graph.invoke(state)
    outputs = response.get("outputs", {})

    # 대화 기록에 사용자 메시지와 응답 추가
    conversation_entry = {"user": user_input}
    conversation_entry.update(outputs)
    st.session_state.conversation.append(conversation_entry)

    # 전체 대화 내역을 다시 렌더링 (새로운 메시지 포함)
    render_conversation()

# 페이지 설정
st.set_page_config(page_title=title, page_icon=icon, layout="wide")
st.header(title)

# 사이드바 영역: Session ID 입력, 대화 기록 초기화, 새 대화하기, 이전 대화 내역 표시
with st.sidebar:
    st.text_input("Session ID", value=st.session_state.session_id, key="session_id_input")
    
    # 대화 기록 초기화 버튼: 불러온 이전 대화가 있다면 conversation_history에서 삭제
    if st.button("대화 기록 초기화"):
        if st.session_state.conversation_loaded_from_history:
            current_session_id = st.session_state.session_id
            # 각 날짜별 대화 목록에서 현재 session_id와 일치하는 대화 삭제
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
    
    # 새 대화하기: 현재 대화가 있다면 (단, 이전 대화에서 불러온 것이 아니라면) 날짜별 히스토리에 저장 후, 새 세션 시작
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
        
        # 새 대화를 위해 현재 대화와 저장소 초기화, 새로운 session_id 생성 및 불러오기 플래그 초기화
        st.session_state.conversation = []
        st.session_state.store = {}
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.conversation_loaded_from_history = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 이전 대화")
    if st.session_state.conversation_history:
        # 최신 날짜가 위에 표시되도록 날짜 내림차순 정렬
        for date_key in sorted(st.session_state.conversation_history.keys(), reverse=True):
            st.markdown(f"#### {date_key}")
            for idx, conv in enumerate(st.session_state.conversation_history[date_key]):
                conv_title = conv["title"]
                conv_time = datetime.fromisoformat(conv["timestamp"]).strftime("%H:%M:%S")
                # 버튼 클릭 시 해당 대화 내역과 session_id를 불러오고, 불러왔다는 플래그 설정
                if st.button(f"{conv_title} ({conv_time})", key=f"{date_key}_{idx}"):
                    st.session_state.conversation = conv["conversation"]
                    st.session_state.session_id = conv["session_id"]
                    st.session_state.conversation_loaded_from_history = True
                    st.rerun()
    else:
        st.write("저장된 대화가 없습니다.")

# 메인 채팅 메시지 영역: 로드된 대화 내역 먼저 렌더링
render_conversation()

# 사용자 입력창: 메시지 입력 시 generate_message() 호출
if prompt := st.chat_input("메세지를 입력해주세요!", key="prompt"):
    generate_message(prompt)
