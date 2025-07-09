from langchain_core.messages import HumanMessage

from advanced_search.graph import graph

def stream_chat(user_text: str) -> None:
    state = {"messages": [HumanMessage(content=user_text)]}

    for update in graph.stream(state, stream_mode="values"):
        if "messages" in update:
            if update["messages"][-1].content != user_input:
                print("Assistant:", update["messages"][-1].content)


print("Type your question (exit / quit to leave)\n")
while True:
    user_input = input("User: ").strip()

    if user_input.lower() in {"exit", "quit", "q"}:
        print("Goodbye!")
        break

    stream_chat(user_input)