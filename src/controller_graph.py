import os

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.checkpoint.sqlite import SqliteSaver

from controller_graph_tools import tavily_search, deep_research
from controller_graph_prompts import user_input_prompt, tavily_analyse_prompt

from datetime import datetime

# State for the advanced_search
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# Defining the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_retries=2,
    api_key=os.getenv("GEMINI_API_KEY"),
)

tools = [tavily_search, deep_research]
llm = llm.bind_tools(tools)



def chatbot(state: State):

    # If the deep_research tool outputs its answer, it is already formatted correctly by the node finalize_answer and so
    # does not need to be fed back into another llm.
    if state["messages"][-1].name == "deep_research":
        return {}



    # If the last message is from the user, the chatbot decides whether to call a tool, or to answer without a tool.
    elif user_input == state["messages"][-1].content:
        formatted_prompt = user_input_prompt.format(
            current_date=datetime.now().strftime("%B %d, %Y"),
            user_input=user_input,
            messages = state["messages"],
        )

    # The chatbot evaluates whether the result from tavily is adequate and either passes on the information to the user
    # or it can call either tavily_search or deep_research to fill the knowledge gap.
    else:
        formatted_prompt = tavily_analyse_prompt.format(
            current_date=datetime.now().strftime("%B %d, %Y"),
            user_input=user_input,
            messages=state["messages"],
            search_result = state["messages"][-1].content,
        )
    message = llm.invoke(formatted_prompt)
    return {"messages": [message]}


tool_node = ToolNode(tools=tools)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

with SqliteSaver.from_conn_string("chat.db") as checkpointer:

    graph = graph_builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}

    def stream_graph_updates(user_input: str):
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config, stream_mode="values"):
            # Ensuring that only strings intended for the user are printed to the user.
            if event["messages"][-1].content != "":
                if event["messages"][-1].content != user_input and event["messages"][-1].content[0] != "{":
                    print("Assistant:", event["messages"][-1].content)

    while True:

        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)

