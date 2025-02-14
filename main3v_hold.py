import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_upstage import ChatUpstage

# 새로 추가: Tavily 검색 도구 임포트 (최대 결과 5개, 한국어)
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

# Define state
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    # 선택된 노드 목록과 최종 출력 저장, 그리고 각 도메인별 최신 정보 검색 여부 플래그
    selected_nodes: list
    outputs: dict
    search_latest: dict

# Create the graph
builder = StateGraph(GraphState)

# Create the Upstage LLM (예시에서는 Upstage 사용)
llm = ChatUpstage(
    model="solar-pro",
    temperature=0,
    max_tokens=500,
    timeout=None,
    max_retries=2
)

# Tavily 검색 도구 생성 (최대 결과 5개, 한국어)
tavily_tool = TavilySearchResults(max_results=5, language="ko")

# 기본 노드 실행 함수 (LLM 호출)
def create_node(state, system_prompt):
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
    system_message = [SystemMessage(content=system_prompt)]
    messages = system_message + human_messages + ai_messages
    response = llm.invoke(messages)
    state["messages"].append(response)
    return state

# 개별 노드들 (전문가 노드)
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

# 1. 라우터 노드: 사용자 메시지에서 관련 항목과 도메인별 최신 정보 검색 요청 여부 판단
def router_node(state):
    user_message = next((msg.content for msg in state["messages"] if isinstance(msg, HumanMessage)), "")
    prompt = (
        "다음 사용자 메시지를 읽고, 그 안에 포함된 주요 항목과 각 항목별 최신 정보 검색 요청 여부를 판단하세요.\n\n"
        "사용자가 메시지에서 아래와 같은 다양한 표현을 사용할 수 있습니다.\n"
        "- **날씨**: '날씨', '기상', '비 오나요?', '맑은가요?', '흐리다' 등\n"
        "- **숙박**: '숙박', '호텔', '잠자는 곳', '객실' 등\n"
        "- **식당**: '식당', '맛집', '음식점', '다이닝' 등\n"
        "- **교통**: '교통', '이동', '타야 할 교통수단', '버스', '지하철' 등\n\n"
        "만약 최신 정보가 필요하면, 각 항목에 대해 '최신 정보를 검색'이라는 문구를 포함해서 출력하세요.\n"
        "예를 들어, 사용자 메시지가 '오늘 날씨 어때? 최신 날씨 정보를 검색해줘, 근처 맛집 어때? 최신 정보를 검색해줘.'라면 "
        "답변은 '날씨 최신 정보를 검색,식당 최신 정보를 검색'과 같이 출력되어야 합니다.\n\n"
        f"사용자 메시지: {user_message}"
    )
    system_message = SystemMessage(content=prompt)
    response = llm.invoke([system_message])
    
    keywords = [kw.strip() for kw in response.content.split(",")]
    mapping = {
        "날씨": "weather",
        "숙박": "hotels",
        "식당": "restaurants",
        "교통": "transportation"
    }
    selected = []
    search_latest = {}
    for kw in keywords:
        # 각 키워드에서 해당 도메인 이름이 포함되어 있는지 확인
        for domain_key, node_name in mapping.items():
            if domain_key in kw:
                # 만약 키워드에 '최신'이라는 단어가 포함되어 있다면 최신 정보 검색 요청으로 처리
                if "최신" in kw:
                    selected.append(node_name)
                    search_latest[node_name] = True
                else:
                    selected.append(node_name)
                    # 최신 정보 검색 요청이 없는 경우 False
                    if node_name not in search_latest:
                        search_latest[node_name] = False
    state["selected_nodes"] = list(dict.fromkeys(selected))
    state["search_latest"] = search_latest
    return state

# 2. 동적 실행 노드: 라우터에서 선택한 노드들만 실행
def dynamic_node(state):
    outputs = {}
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

# 3. 최신 정보 보충 노드: 각 도메인별 최신 정보 검색 플래그가 True이면 개별 검색 수행
def tavily_node(state):
    outputs = state.get("outputs", {})
    tavily_results = {}
    for domain in ["weather", "hotels", "restaurants", "transportation"]:
        ans = outputs.get(domain, "정보 없음")
        # 기본 결과는 기존 답변 그대로 사용
        result = ans  
        if state.get("search_latest", {}).get(domain, False):
            # 최신 정보 검색 요청이 있으면 해당 도메인에 대해 최신 정보 검색 수행
            search_results = tavily_tool.run(f"{domain} 최신 정보")
            search_info = "\n".join(search_results)
            result += "\n\n--- 최신 검색 결과 ---\n" + search_info
        tavily_results[domain] = result

    outputs["tavily"] = tavily_results
    state["outputs"] = outputs
    ai_message = AIMessage(content=str(tavily_results))
    state["messages"].append(ai_message)
    return state

# 노드 등록
builder.add_node("router", router_node)
builder.add_node("dynamic", dynamic_node)
builder.add_node("tavily", tavily_node)

# 엣지 구성: START -> router -> dynamic -> tavily -> END
builder.add_edge(START, "router")
builder.add_edge("router", "dynamic")
builder.add_edge("dynamic", "tavily")
builder.add_edge("tavily", END)

# 그래프 빌드
graph = builder.compile()

# Draw the graph (mermaid 이미지로 출력)
try:
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph3v.png")
except Exception:
    pass

# main_loop: 터미널에서 사용자 입력을 처리하여 각 노드의 결과를 출력
def main_loop():
    while True:
        user_input = input(">> ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # 초기 상태: HumanMessage, 빈 selected_nodes, outputs, 최신 정보 플래그 초기값 설정
        state = {
            "messages": [HumanMessage(content=user_input)],
            "selected_nodes": [],
            "outputs": {},
            "search_latest": {}
        }
        result = graph.invoke(state)
        outputs = result.get("outputs", {})
        if "weather" in outputs:
            print(f"weather: {outputs['weather']}")
        if "hotels" in outputs:
            print(f"hotels: {outputs['hotels']}")
        if "restaurants" in outputs:
            print(f"restaurants: {outputs['restaurants']}")
        if "transportation" in outputs:
            print(f"transportation: {outputs['transportation']}")
        if "tavily" in outputs:
            print("tavily (최신 정보 보충):")
            for domain, res in outputs["tavily"].items():
                print(f"  {domain}: {res}")

if __name__ == "__main__":
    main_loop()
