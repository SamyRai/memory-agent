"""Memory Agent State Management."""

from __future__ import annotations
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated
from typing import List, Optional


def add_retrieved_document(docs: List[str], new_doc: str) -> List[str]:
    """Reducer to append retrieved documents."""
    if new_doc:
        docs.append(new_doc)
    return docs


def add_tool_output(outputs: List[str], new_output: str) -> List[str]:
    """Reducer to append tool outputs."""
    if new_output:
        outputs.append(new_output)
    return outputs


@dataclass(kw_only=True)
class AgentState:
    """State structure for the Memory Agent workflow."""
    next_step: Optional[str] = None
    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    retrieved_documents: Annotated[List[str], add_retrieved_document] = field(default_factory=list)
    tool_outputs: Annotated[List[str], add_tool_output] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    final_response: Optional[str] = None
    iteration_count: int = 0
