"""Configuration module for Memory Agent."""

import os
from dataclasses import dataclass, field, fields
from typing import Optional
from langchain_core.runnables import RunnableConfig
from memory_agent import prompts


@dataclass(kw_only=True)
class Configuration:
    """Configuration class for Memory Agent."""

    user_id: str = "default"
    model: str = field(
        default="ollama/llama3.1-8b",
        metadata={
            "description": "LLM model identifier. Format: provider/model-name."
        },
    )
    system_prompt: str = prompts.SYSTEM_PROMPT

    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Load configuration from RunnableConfig or environment variables."""
        configurable = config.get("configurable", {}) if config else {}
        values = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        # Only pass values that are not None
        return cls(**{k: v for k, v in values.items() if v is not None})
