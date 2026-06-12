"""Define the Memory Agent workflow graph with enforced tool decision."""

import asyncio
import json
import logging
from datetime import datetime
<<<<<<< Updated upstream
from typing import cast

from langgraph.graph import END, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore

from memory_agent import tools, utils
from memory_agent.context import Context
from memory_agent.state import State
=======
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from ollama import Client
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore
from memory_agent.tools import document_search, workday_tool, upsert_memory
from memory_agent.configuration import Configuration
from memory_agent.state import AgentState
>>>>>>> Stashed changes

# Initialize logging
logger = logging.getLogger(__name__)

<<<<<<< Updated upstream

async def call_model(state: State, runtime: Runtime[Context]) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    user_id = runtime.context.user_id
    model = runtime.context.model
    system_prompt = runtime.context.system_prompt

    # Retrieve the most recent memories for context
    memories = await cast(BaseStore, runtime.store).asearch(
        ("memories", user_id),
        query=str([m.content for m in state.messages[-3:]]),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(
        f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
    )
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>"""

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = system_prompt.format(user_info=formatted, time=datetime.now().isoformat())

    # Load the chat model from the runtime context
    llm = utils.load_chat_model(model)

    # Invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how
    # to use them.
    msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
        [{"role": "system", "content": sys}, *state.messages]
    )
    return {"messages": [msg]}


async def store_memory(state: State, runtime: Runtime[Context]):
    # Extract tool calls from the last message
    tool_calls = getattr(state.messages[-1], "tool_calls", [])

    # Concurrently execute all upsert_memory calls
    saved_memories = await asyncio.gather(
        *(
            tools.upsert_memory(
                **tc["args"],
                user_id=runtime.context.user_id,
                store=cast(BaseStore, runtime.store),
            )
            for tc in tool_calls
        )
=======
# Initialize memory store
store = InMemoryStore(
    index={"embed": lambda x: x, "dims": 384}
)

# Define available tools for invocation
AVAILABLE_TOOLS = {
    "document_search": document_search,
    "workday_tool": workday_tool,
}

# Define tools metadata for the model
TOOLS_METADATA = [
    {
        "name": "document_search",
        "description": "Search for documents related to a query.",
        "parameters": {
            "query": {"type": "string", "description": "The search query."},
        },
    },
    {
        "name": "workday_tool",
        "description": "Interact with the Workday system.",
        "parameters": {
            "action": {"type": "string", "description": "The action to perform in Workday."},
            "parameters": {"type": "object", "description": "Parameters for the action."},
        },
    },
]


async def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
    """Call the model to decide the next step: retrieval, tool usage, or final response."""
    
    recent_messages = state.messages[-3:]

    # Fetch memory from storage
    user_id = config.get("user_id", "default_user")
    memories = await store.asearch(
        ("memories", user_id),
        query=" ".join(m.content for m in recent_messages),
        limit=10,
    )

    formatted_memories = [{"key": m.key, "value": m.value} for m in memories]

    system_prompt = json.dumps({
        "instructions": (
            "Analyze the user request and determine the best action:\n"
            "- If specific information is needed, choose an available tool.\n"
            "- If previous memory can help, use it.\n"
            "- Otherwise, generate a response directly.\n"
        ),
        "available_tools": TOOLS_METADATA,  # ✅ Pass available tools to the model
        "memories": formatted_memories,
        "retrieved_docs": state.retrieved_documents,
        "tool_outputs": state.tool_outputs,
        "time": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2)

    client = Client(host="http://host.docker.internal:11434")

    # Call the model with tool options
    response = client.chat(
        model="llama3.1:latest",
        messages=[{"role": "system", "content": system_prompt}]
        + [{"role": "user", "content": msg.content} for msg in recent_messages],
        format="json",
    )

    try:
        parsed_response = json.loads(response["message"]["content"])
        state.final_response = parsed_response.get("text", response["message"]["content"])

        # 🚨 **Ensure tool decision is explicitly parsed**
        if "tool_calls" in parsed_response:
            state.next_step = "tool_decision"
        else:
            state.next_step = "finalize_response"

    except json.JSONDecodeError:
        logger.error("🚨 Failed to parse model response. Using raw output.")
        state.final_response = response["message"]["content"]
        state.next_step = "finalize_response"

    state.messages.append(AIMessage(content=state.final_response))
    return state


async def tool_decision(state: AgentState, config: RunnableConfig) -> AgentState:
    """Decides whether tools need to be invoked before finalizing the response."""
    
    try:
        parsed_response = json.loads(state.final_response)

        if "tool_calls" in parsed_response:
            state.messages.append(AIMessage(content="Tool invocation required"))
            state.tool_calls = parsed_response["tool_calls"]
            state.next_step = "invoke_tool"
        else:
            state.next_step = "finalize_response"

    except json.JSONDecodeError:
        logger.error("🚨 Failed to parse tool decision. Proceeding to finalize response.")
        state.next_step = "finalize_response"

    return state


async def invoke_tool(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute requested tools and return to model for further steps."""

    for tool_call in state.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})

        if tool_name in AVAILABLE_TOOLS:
            tool_function = AVAILABLE_TOOLS[tool_name]
            result = await tool_function(**tool_args) if asyncio.iscoroutinefunction(tool_function) else tool_function(**tool_args)
            state.tool_outputs.append(str(result))
        else:
            logger.warning(f"🚨 Tool '{tool_name}' is not defined.")

    state.next_step = "call_model"  # 🔄 Loop back to refine response with tool results
    return state


async def finalize_response(state: AgentState, config: RunnableConfig) -> AgentState:
    """Final step: Model reflects on everything and gives the best possible answer."""
    
    system_prompt = json.dumps({
        "final_summary": "Review all retrieved information and produce the best response.",
        "memories": state.retrieved_documents,
        "tool_outputs": state.tool_outputs,
        "time": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2)

    client = Client(host="http://host.docker.internal:11434")

    response = client.chat(
        model="llama3.1:latest",
        messages=[{"role": "system", "content": system_prompt}]
        + [{"role": "user", "content": msg.content} for msg in state.messages],
        format="json",
>>>>>>> Stashed changes
    )

    state.final_response = response["message"]["content"]
    state.messages.append(AIMessage(content=state.final_response))
    state.next_step = "store_memory"
    return state


<<<<<<< Updated upstream
def route_message(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    if getattr(msg, "tool_calls", None):
        # If there are tool calls, we need to store memories
        return "store_memory"
    # Otherwise, finish; user can send the next message
    return END


# Create the graph + all nodes
builder = StateGraph(State, context_schema=Context)
=======
async def store_memory(state: AgentState, config: RunnableConfig) -> AgentState:
    """Store conversation context in memory before finishing."""
    
    user_id = Configuration.from_runnable_config(config).user_id or "default_user"

    if not user_id.strip():
        logger.warning("🚨 Empty user_id detected. Using 'default_user'.")
        user_id = "default_user"

    await upsert_memory(
        content=state.final_response,
        context="Generated AI response",
        config=config,
        store=store,
        memory_id=None,
        user_id=user_id,
    )
    return state


# ---- Graph Construction ----
builder = StateGraph(state_schema=AgentState)

# Add main iterative nodes
builder.add_node("call_model", call_model)
builder.add_node("tool_decision", tool_decision)  # ✅ New node to decide tool usage
builder.add_node("invoke_tool", invoke_tool)
builder.add_node("finalize_response", finalize_response)
builder.add_node("store_memory", store_memory)

# Define edges
builder.add_edge(START, "call_model")
builder.add_conditional_edges(
    "call_model", lambda state: state.next_step, ["tool_decision", "finalize_response"]
)
builder.add_conditional_edges(
    "tool_decision", lambda state: state.next_step, ["invoke_tool", "finalize_response"]
)
builder.add_edge("invoke_tool", "call_model")  # 🔄 Loop back to refine response
builder.add_edge("finalize_response", "store_memory")
builder.add_edge("store_memory", END)
>>>>>>> Stashed changes

graph = builder.compile()
graph.name = "MemoryAgent"

__all__ = ["graph"]
