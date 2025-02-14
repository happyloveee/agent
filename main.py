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
    messages = llm.invoke(messages)
    return {"messages": [messages]}

# Analyst node
weather = lambda state: create_node(
    state, 
    "당신은 날씨 예보자입니다. 제공된 지침을 검토한 후, 사용자가 이해할 수 있는 명확하고 구체적인 날씨 예보를 작성하세요. "
    "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
    "맑음이: **날씨를 알려드리는 맑음이에요!**\n\n"
    "그 후, 자세한 날씨 정보를 제공하세요."
)

# Architect node
hotels = lambda state: create_node(
    state,
    "당신은 숙박 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 숙박 옵션을 추천하는 상세 정보를 작성하세요. "
    "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
    "숙박이: **숙박을 추천해 주는 숙박이에요!**\n\n"
    "그 후, 구체적인 추천 내용을 제공하세요."
)

# Architect node
restaurants = lambda state: create_node(
    state,
    "당신은 식당 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 식당 옵션을 추천하는 상세 정보를 작성하세요. "
    "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
    "맛탕: **맛있는 식당을 추천해주는 맛탕이에요!**\n\n"
    "그 후, 구체적인 추천 내용을 제공하세요."
)

# Architect node
transportation = lambda state: create_node(
    state,
    "당신은 교통편 추천 전문가입니다. 제공된 사용자의 요구사항을 검토한 후, 사용자가 만족할 수 있는 최적의 교통편 옵션을 추천하는 상세 정보를 작성하세요. "
    "응답은 반드시 다음 헤더로 시작해야 합니다:\n\n"
    "타고: **교통편을 추천하는 타고에요!**\n\n"
    "그 후, 구체적인 추천 내용을 제공하세요."
)

# Add nodes to the graph
builder.add_node("weather", weather)
builder.add_node("hotels", hotels)
builder.add_node("restaurants", restaurants)
builder.add_node("transportation", transportation)

# Set entry point and edges
builder.add_edge(START, "weather")
builder.add_edge("weather", "hotels")
builder.add_edge("hotels", "restaurants")
builder.add_edge("restaurants", "transportation")
builder.add_edge("transportation", END)

# Build the graph
graph = builder.compile()

# Draw the graph
try:
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
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
        
        response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        print(f"weather: {response['messages'][-4].content}")
        print(f"hotels: {response['messages'][-3].content}")
        print(f"restaurants: {response['messages'][-2].content}")
        print(f"transportation: {response['messages'][-1].content}")

# Run the main loop
if __name__ == "__main__":
    main_loop()
