from __future__ import annotations

from typing import Dict, List, Any, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, MessagesState
from langchain_openai import AzureChatOpenAI
import os


class ChatState(MessagesState):
    """MessagesState-compatible chat state."""
    pass


def _build_model() -> AzureChatOpenAI:
    """
    Build an Azure OpenAI chat model instance.

    Expected environment variables:
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_DEPLOYMENT
    - AZURE_OPENAI_API_VERSION
    """
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    if not all([deployment, api_key, endpoint]):
        raise RuntimeError(
            "Azure OpenAI environment variables are not fully set. "
            "Please configure AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_KEY, "
            "and AZURE_OPENAI_ENDPOINT."
        )

    return AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )


def build_chat_graph():
    """Create a very small LangGraph with memory over messages."""

    model = _build_model()

    def call_model(state: ChatState, config: RunnableConfig) -> ChatState:
        response = model.invoke(state["messages"], config=config)
        return {"messages": [response]}

    workflow = StateGraph(ChatState)
    workflow.add_node("chat", call_model)
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)

    graph = workflow.compile()
    return graph

