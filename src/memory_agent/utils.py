"""Utility functions for Memory Agent."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

<<<<<<< Updated upstream

def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider)
=======
def split_model_and_provider(model_name: str) -> dict:
    """Extract provider and model from full model name."""
    if "/" in model_name:
        provider, model = model_name.split("/", maxsplit=1)
    else:
        provider = None
        model = model_name
    return {"model": model, "provider": provider}
>>>>>>> Stashed changes
