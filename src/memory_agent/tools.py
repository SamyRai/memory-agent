"""Define tools used in Memory Agent with Airbyte API integration."""

import uuid
<<<<<<< Updated upstream
from typing import Annotated

from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore
=======
import requests
import logging
from typing import Annotated, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.store.base import BaseStore
from memory_agent.configuration import Configuration

# Initialize logging
logger = logging.getLogger(__name__)

# Airbyte & Weaviate API details
AIRBYTE_API_BASE_URL = "http://localhost:8000/api/v1"
AIRBYTE_CONNECTION_ID = "your_airbyte_connection_id"
AIRBYTE_SYNC_ENDPOINT = f"{AIRBYTE_API_BASE_URL}/connections/sync"
AIRBYTE_READ_ENDPOINT = f"{AIRBYTE_API_BASE_URL}/connections/{AIRBYTE_CONNECTION_ID}/read"
WEAVIATE_SEARCH_ENDPOINT = "http://weaviate:8080/v1/graphql"  # Update if needed

@tool
def document_search(query: str) -> dict:
    """
    Fetches relevant documents from Weaviate via Airbyte using a semantic query.

    Args:
        query (str): The search query for retrieving relevant documents.

    Returns:
        dict: Retrieved documents with metadata.
    """
    try:
        # Step 1: Trigger Airbyte Sync (optional)
        sync_response = requests.post(
            AIRBYTE_SYNC_ENDPOINT, json={"connectionId": AIRBYTE_CONNECTION_ID}, timeout=30
        )
        if sync_response.status_code not in [200, 202]:
            raise Exception(f"Failed to trigger sync: {sync_response.json()}")

        # Step 2: Query Weaviate for relevant documents
        weaviate_query = {
            "query": f"""
            {{
                Get {{
                    Document(
                        nearText: {{ concepts: ["{query}"] }},
                        limit: 5
                    ) {{
                        title
                        content
                        metadata {{
                            source
                            timestamp
                        }}
                    }}
                }}
            }}
            """
        }

        weaviate_response = requests.post(WEAVIATE_SEARCH_ENDPOINT, json=weaviate_query, timeout=30)
        if weaviate_response.status_code != 200:
            raise Exception(f"Failed to fetch Weaviate data: {weaviate_response.json()}")

        # Step 3: Extract relevant documents
        response_data = weaviate_response.json()
        documents = response_data.get("data", {}).get("Get", {}).get("Document", [])

        # Format the response
        structured_docs = [
            {
                "title": doc["title"],
                "text": doc["content"],
                "source": doc["metadata"].get("source", "unknown"),
                "timestamp": doc["metadata"].get("timestamp", "unknown"),
            }
            for doc in documents
        ]

        logger.info(f"Retrieved {len(structured_docs)} documents for query: {query}")
        return {"documents": structured_docs}

    except Exception as e:
        logger.error(f"Error fetching Weaviate data via Airbyte: {e}")
        return {"error": str(e), "documents": []}


@tool
def workday_tool(action: str, parameters: dict) -> str:
    """Interact with the Workday system."""
    return f"Workday action '{action}' executed with parameters: {parameters}"
>>>>>>> Stashed changes


async def upsert_memory(
    content: str,
    context: str,
    *,
<<<<<<< Updated upstream
    memory_id: uuid.UUID | None = None,
    # Hide these arguments from the model.
    user_id: Annotated[str, InjectedToolArg],
    store: Annotated[BaseStore, InjectedToolArg],
=======
    memory_id: Optional[uuid.UUID] = None,
    config: Annotated[RunnableConfig, "InjectedToolArg"],
    store: Annotated[BaseStore, "InjectedToolArg"],
    user_id: Optional[str] = None,  # Pass user_id explicitly
>>>>>>> Stashed changes
):
    """Upsert memory with a unique ID."""
    user_id = user_id or Configuration.from_runnable_config(config).user_id or "default_user"

    if not user_id.strip():
        logger.warning("Empty user_id detected. Using 'default_user'.")
        user_id = "default_user"

    mem_id = memory_id or uuid.uuid4()
<<<<<<< Updated upstream
    await store.aput(
        ("memories", user_id),
        key=str(mem_id),
        value={"content": content, "context": context},
    )
    return f"Stored memory {mem_id}"
=======

    await store.aput(("memories", user_id), key=str(mem_id), value={"content": content, "context": context})
    return f"Memory stored with ID: {mem_id}"
>>>>>>> Stashed changes
