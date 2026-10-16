"""Fixture: graph with a conditional edge and a loop, no API keys needed."""
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    text: str
    count: int
    kind: str


def classify(state: State) -> dict:
    return {"kind": "question" if state.get("text", "").endswith("?") else "statement", "count": state.get("count", 0)}


def answer(state: State) -> dict:
    return {"text": "answer to: " + state["text"]}


def echo(state: State) -> dict:
    return {"text": state["text"] + "!", "count": state.get("count", 0) + 1}


def route(state: State) -> Literal["answer", "echo"]:
    return "answer" if state["kind"] == "question" else "echo"


def again(state: State) -> Literal["echo", "__end__"]:
    if state.get("text", "") == "boom!":
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return "echo" if state["count"] < 2 else END


b = StateGraph(State)
b.add_node(classify); b.add_node(answer); b.add_node(echo)
b.add_edge(START, "classify")
b.add_conditional_edges("classify", route)
b.add_conditional_edges("echo", again)
b.add_edge("answer", END)
graph = b.compile(name="Fixture Router")
