import os
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_upstage import ChatUpstage

load_dotenv()

# Define state
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    # 추가: 선택된 노드 리스트와 최종 출력 저장
    selected_nodes: list
    outputs: dict

# Create the graph
builder = StateGraph(GraphState)

# Create the Upstage LLM
llm = ChatUpstage(
    model = "solar-pro",
    temperature = 0,
    max_tokens = 500,
    timeout = None,
    max_retries = 2
)

# # Create the OpenAI LLM
# llm = ChatOpenAI(
#     model="gpt-4o",
#     temperature=0,
#     max_tokens=500,
#     timeout=None,
#     max_retries=2
# )

def create_node(state, system_prompt):
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
    system_message = [SystemMessage(content=system_prompt)]
    messages = system_message + human_messages + ai_messages
    response = llm.invoke(messages)
    state["messages"].append(response)
    return state

# 개별 노드들
def weather_node(state):
    prompt = (
        "당신은 날씨 예보자입니다. 제공된 지침을 검토한 후, 사용자가 이해할 수 있는 명확하고 구체적인 날씨 예보를 작성하세요. "
        "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
        "맑음이: **날씨를 알려드리는 맑음이에요!**\n\n"
        "그 후, 자세한 날씨 정보를 제공하세요."
    )
    return create_node(state, prompt)

def hotels_node(state):
    prompt = (
        "당신은 숙박 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 숙박 옵션을 추천하는 상세 정보를 작성하세요. "
        "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
        "숙박이: **숙박을 추천해 주는 숙박이에요!**\n\n"
        "그 후, 구체적인 추천 내용을 제공하세요."
    )
    return create_node(state, prompt)

def restaurants_node(state):
    prompt = (
        "당신은 식당 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 식당 옵션을 추천하는 상세 정보를 작성하세요. "
        "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
        "맛탕: **맛있는 식당을 추천해주는 맛탕이에요!**\n\n"
        "그 후, 구체적인 추천 내용을 제공하세요."
    )
    return create_node(state, prompt)

def transportation_node(state):
    prompt = (
        "당신은 교통편 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 교통편 옵션을 추천하는 상세 정보를 작성하세요. "
        "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
        "타고: **교통편을 추천하는 타고에요!**\n\n"
        "그 후, 구체적인 추천 내용을 제공하세요."
    )
    return create_node(state, prompt)


def router_node(state):
    # 사용자 입력 중 첫번째 HumanMessage를 가져 옵니다.
    user_message = next((msg.content for msg in state["messages"] if isinstance(msg, HumanMessage)), "")

    prompt = (
    "다음 사용자 메시지를 읽고, 그 안에 포함된 주요 항목을 판단하세요. 판단해야 할 항목은 '날씨', '숙박', '식당', '교통'입니다.\n\n"
    "사용자가 메시지에서 아래와 같은 다양한 표현을 사용할 수 있습니다.\n"
    "- **날씨**: '날씨', '기상', '비 오나요?', '맑은가요?', '흐리다' 등\n"
    "- **숙박**: '숙박', '호텔', '잠자는 곳', '객실' 등\n"
    "- **식당**: '식당', '맛집', '음식점', '다이닝' 등\n"
    "- **교통**: '교통', '이동', '타야 할 교통수단', '버스', '지하철' 등\n\n"
    "답변은 해당 항목의 이름만 정확하게, 쉼표로 구분하여 출력하세요. 예를 들어, 사용자 메시지에 날씨와 식당 관련 표현이 모두 있다면 "
    "답변은 '날씨,식당'과 같이 출력해야 합니다.\n\n"
    f"사용자 메시지: {user_message}"
)
    system_message = SystemMessage(content=prompt)
    response = llm.invoke([system_message])
    
    # LLM의 응답에서 키워드를 쉼표 기준으로 분리합니다.
    keywords = [kw.strip() for kw in response.content.split(",")]
    # 키워드를 해당 노드 이름으로 매핑
    mapping = {
        "날씨": "weather",
        "숙박": "hotels",
        "식당": "restaurants",
        "교통": "transportation"
    }
    selected = [mapping[kw] for kw in keywords if kw in mapping]
    # 중복 제거 후 상태에 저장
    state["selected_nodes"] = list(dict.fromkeys(selected))
    return state


# 2. 동적 실행 노드: 라우터에서 선택한 노드들만 실행
def dynamic_node(state):
    outputs = {}
    # 선택된 노드에 따라 실행
    for node in state.get("selected_nodes", []):
        if node == "weather":
            state = weather_node(state)
            outputs["weather"] = state["messages"][-1].content
        elif node == "hotels":
            state = hotels_node(state)
            outputs["hotels"] = state["messages"][-1].content
        elif node == "restaurants":
            state = restaurants_node(state)
            outputs["restaurants"] = state["messages"][-1].content
        elif node == "transportation":
            state = transportation_node(state)
            outputs["transportation"] = state["messages"][-1].content
    state["outputs"] = outputs
    return state

# 노드 등록
builder.add_node("router", router_node)
builder.add_node("dynamic", dynamic_node)
# (개별 노드들은 동적 노드 내에서 호출하므로 별도 엣지 등록 불필요)

# 엣지 구성: 시작 -> 라우터 -> 동적 실행 -> 종료
builder.add_edge(START, "router")
builder.add_edge("router", "dynamic")
builder.add_edge("dynamic", END)


# Build the graph
graph = builder.compile()

# Draw the graph
try:
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph2v.png")
except Exception:
    pass

# Create a main loop
def main_loop():
    # Run the Chatbot
    while True:
        user_input = input(">> ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # 초기 상태: messages에 HumanMessage를 넣고 selected_nodes, outputs 초기화
        state = {"messages": [HumanMessage(content=user_input)], "selected_nodes": [], "outputs": {}}
        result = graph.invoke(state)
        outputs = result.get("outputs", {})
        # 선택된 각 노드의 결과 출력
        for key, content in outputs.items():
            print(f"{key}: {content}")

# Run the main loop
if __name__ == "__main__":
    main_loop()




