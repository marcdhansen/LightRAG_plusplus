"""
DSPy Configuration for LightRAG Integration

This module handles the setup and configuration of DSPy for use within LightRAG,
ensuring compatibility with existing LLM configurations and optimization targets.
"""

import os
from pathlib import Path
from typing import Any

import dspy


class DSPyConfig:
    """Configuration manager for DSPy integration with LightRAG."""

    def __init__(self):
        self.lightrag_config = self._load_lightrag_config()
        self.dspy_config = self._setup_dspy_config()

    def _load_lightrag_config(self) -> dict[str, Any]:
        """Load existing LightRAG configuration to maintain compatibility."""
        config = {}

        # Check for common environment variables used by LightRAG
        if os.getenv("OPENAI_API_KEY"):
            config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
            config["openai_model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if os.getenv("ANTHROPIC_API_KEY"):
            config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
            config["anthropic_model"] = os.getenv(
                "ANTHROPIC_MODEL", "claude-3-sonnet-20240229"
            )

        if os.getenv("OLLAMA_HOST"):
            config["ollama_host"] = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            config["ollama_model"] = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

        return config

    def _setup_dspy_config(self) -> dict[str, Any]:
        """Setup DSPy-specific configuration."""
        config = {
            "cache": True,  # Enable DSPy caching for optimization
            "experimental": {
                "enable_gepa": True,  # Enable GEPA optimizer
                "enable_mipro": True,  # Enable MIPROv2 optimizer
            },
            "optimization": {
                "max_threads": 4,  # Conservative thread usage
                "max_bootstrapped_demos": 3,  # Few-shot examples for optimization
                "max_labeled_demos": 2,  # Labeled examples for optimization
                "auto_mode": "light",  # Use light mode for faster optimization
            },
        }
        return config

    def configure_dspy_lm(
        self, model_name: str | None = None, provider: str | None = None
    ) -> dspy.LM:
        """Configure DSPy LM based on existing LightRAG settings."""

        if model_name and provider:
            # Use explicit model configuration
            return self._create_lm_from_explicit_config(model_name, provider)
        else:
            # Auto-detect from environment
            return self._create_lm_from_environment()

    def _create_lm_from_explicit_config(
        self, model_name: str, provider: str
    ) -> dspy.LM:
        """Create DSPy LM from explicit model configuration."""

        if provider.lower() == "openai":
            api_key = self.lightrag_config.get("openai_api_key") or os.getenv(
                "OPENAI_API_KEY"
            )
            if not api_key:
                raise ValueError("OpenAI API key not found")
            return dspy.LM(f"openai/{model_name}", api_key=api_key)

        elif provider.lower() == "anthropic":
            api_key = self.lightrag_config.get("anthropic_api_key") or os.getenv(
                "ANTHROPIC_API_KEY"
            )
            if not api_key:
                raise ValueError("Anthropic API key not found")
            return dspy.LM(f"anthropic/{model_name}", api_key=api_key)

        elif provider.lower() == "ollama":
            api_base = (
                self.lightrag_config.get("ollama_host") or "http://localhost:11434"
            )
            return dspy.LM(f"ollama_chat/{model_name}", api_base=api_base, api_key="")

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _create_lm_from_environment(self) -> dspy.LM:
        """Auto-detect and create LM from environment variables."""

        # Priority: OpenAI > Anthropic > Ollama
        if self.lightrag_config.get("openai_api_key"):
            model = self.lightrag_config.get("openai_model", "gpt-4o-mini")
            api_key = self.lightrag_config["openai_api_key"]
            return dspy.LM(f"openai/{model}", api_key=api_key)

        elif self.lightrag_config.get("anthropic_api_key"):
            model = self.lightrag_config.get(
                "anthropic_model", "claude-3-sonnet-20240229"
            )
            api_key = self.lightrag_config["anthropic_api_key"]
            return dspy.LM(f"anthropic/{model}", api_key=api_key)

        elif self.lightrag_config.get("ollama_host"):
            model = self.lightrag_config.get("ollama_model", "llama3.2:1b")
            api_base = self.lightrag_config["ollama_host"]
            return dspy.LM(f"ollama_chat/{model}", api_base=api_base, api_key="")

        else:
            raise ValueError("No supported LLM configuration found in environment")

    def configure_dspy(
        self, model_name: str | None = None, provider: str | None = None
    ) -> None:
        """Configure DSPy with LM and settings."""

        # Create and configure LM
        lm = self.configure_dspy_lm(model_name, provider)

        # Configure DSPy with the LM and cache settings
        settings = {
            "lm": lm,
        }

        # Add caching configuration
        if self.dspy_config["cache"]:
            settings["cache"] = True

        dspy.configure(**settings)

    def get_optimizer_config(self, optimizer_name: str) -> dict[str, Any]:
        """Get configuration for specific DSPy optimizer."""

        base_config = self.dspy_config["optimization"].copy()

        if optimizer_name.lower() == "mipro_v2":
            return {
                **base_config,
                "auto": base_config["auto_mode"],
                "num_threads": base_config["max_threads"],
            }

        elif optimizer_name.lower() == "gepa":
            return {
                **base_config,
                "num_threads": base_config["max_threads"],
                "max_rounds": 3,  # GEPA-specific setting
            }

        elif optimizer_name.lower() == "bootstrap_fewshot":
            return {
                **base_config,
                "max_bootstrapped_demos": base_config["max_bootstrapped_demos"],
                "max_labeled_demos": base_config["max_labeled_demos"],
            }

        else:
            return base_config

    @staticmethod
    def get_working_directory() -> Path:
        """Get the working directory for DSPy optimization artifacts."""
        base_dir = Path(__file__).parent.parent.parent
        return base_dir / "lightrag" / "dspy_integration" / "prompts"


# Global configuration instance
_dspy_config = None


def get_dspy_config() -> DSPyConfig:
    """Get the global DSPy configuration instance."""
    global _dspy_config
    if _dspy_config is None:
        _dspy_config = DSPyConfig()
    return _dspy_config


def configure_dspy_from_env() -> None:
    """Configure DSPy from environment variables (convenience function)."""
    config = get_dspy_config()
    config.configure_dspy()
