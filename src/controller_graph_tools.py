from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from advanced_search.graph import graph
from langchain_core.messages import HumanMessage


tavily = TavilySearch(max_results=2)

@tool(
    args_schema={
          "type": "object",
          "properties": {
              "query": {
                  "type": "string",
                  "description":"Question to ask a search engine"
              }
          },
          "required": ["query"]
      },
      description="Tavily web search. Best for single facts, and information that is easily found on the internet."
)

def tavily_search(query: str) -> str:
    return tavily.run(query)

@tool(
    return_direct=True,
      args_schema={
          "type": "object",
          "properties": {
              "query": {
                  "type": "string",
                  "description": "The user's question"}},
          "required": ["query"]
      },
      description=(
              "Advanced multi-step research tool"
              "Use when the question cannot be easily found on the internet, or has sub-questions."
              "Return a short, human readable answer from Tavily."
      )
)

def deep_research(query: str) -> str:
    state = {"messages": [HumanMessage(content=query)]}
    result = graph.invoke(state)
    final_message = result["messages"][-2].content + "\n" + result["messages"][-1].content
    return final_message