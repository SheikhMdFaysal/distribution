from typing import Dict, Any, Optional
import requests
from .base import ModelAdapter


class OllamaAdapter(ModelAdapter):
    """Adapter for local models via Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3", timeout: int = 30, max_retries: int = 3):
        super().__init__(timeout, max_retries)
        self.base_url = base_url
        self.model = model
        self.model_type = "local"
    
    def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response using Ollama API"""
        if params is None:
            params = {}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": params.get("temperature", 0.7),
                        "num_predict": params.get("max_tokens", 1000),
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response_text": data.get("response", ""),
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "ollama",
                    "metadata": {
                        "tokens_used": data.get("eval_count", 0),
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
            else:
                # Fallback to simulated response
                return {
                    "response_text": f"[Simulated Ollama response for: {prompt[:50]}...]",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "ollama",
                    "metadata": {
                        "tokens_used": len(prompt.split()),
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
        except Exception as e:
            # Fallback to simulated response if Ollama is not running
            return {
                "response_text": f"[Simulated Ollama response for: {prompt[:50]}...]",
                "model_name": self.model,
                "model_type": self.model_type,
                "vendor": "ollama",
                "metadata": {
                    "error": str(e),
                    "response_time_ms": 0,
                    "model_version": self.model
                }
            }
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model,
            "model_type": self.model_type,
            "vendor": "ollama"
        }


def create_adapter(model_config: Dict[str, Any]) -> ModelAdapter:
    """Factory function to create appropriate adapter based on config"""
    adapter_type = model_config.get("adapter")
    
    print(f"\n=== [ADAPTER FACTORY] Creating adapter for: {model_config} ===")
    
    # Import here to avoid circular imports
    if adapter_type == "openai":
        from .openai_adapter import OpenAIAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating OpenAI Adapter")
        return OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY or "demo-key",
            model=model_config.get("model", "gpt-4")
        )
    elif adapter_type == "anthropic":
        from .anthropic_adapter import AnthropicAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating Anthropic Adapter")
        return AnthropicAdapter(
            api_key=settings.ANTHROPIC_API_KEY or "demo-key",
            model=model_config.get("model", "claude-3-opus-20240229")
        )
    elif adapter_type == "google":
        from .google_adapter import GoogleAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating Google Adapter")
        return GoogleAdapter(
            api_key=settings.GOOGLE_API_KEY or "demo-key",
            model=model_config.get("model", "gemini-1.5-pro")
        )
    elif adapter_type == "groq":
        from .openai_adapter import OpenAIAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating Groq Adapter (OpenAI-compatible)")
        return OpenAIAdapter(
            api_key=settings.GROQ_API_KEY or "demo-key",
            model=model_config.get("model", "llama-3.1-8b-instant"),
            base_url="https://api.groq.com/openai/v1",
            vendor="groq",
        )
    elif adapter_type == "openrouter":
        from .openai_adapter import OpenAIAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating OpenRouter Adapter (OpenAI-compatible)")
        return OpenAIAdapter(
            api_key=settings.OPENROUTER_API_KEY or "demo-key",
            model=model_config.get("model", "inclusionai/ling-2.6-flash:free"),
            base_url="https://openrouter.ai/api/v1",
            vendor="openrouter",
        )
    elif adapter_type == "huggingface":
        from .openai_adapter import OpenAIAdapter
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating Hugging Face Adapter (OpenAI-compatible)")
        return OpenAIAdapter(
            api_key=settings.HF_TOKEN or "demo-key",
            model=model_config.get("model", "meta-llama/Llama-3.1-8B-Instruct"),
            base_url="https://api-inference.huggingface.co/v1",
            vendor="huggingface",
        )
    elif adapter_type == "custom":
        # Bring Your Own Model — credentials and endpoint provided per-request
        # by the client. Used for testing the customer's own AI deployments.
        from .openai_adapter import OpenAIAdapter
        custom_url = model_config.get("base_url")
        custom_key = model_config.get("api_key", "")
        custom_model = model_config.get("model", "gpt-4")
        custom_vendor = model_config.get("vendor", "custom")
        print(f"[ADAPTER FACTORY] -> Creating Custom (BYOM) Adapter for {custom_url}")
        if not custom_url:
            raise ValueError("BYOM adapter requires base_url in model_config")
        return OpenAIAdapter(
            api_key=custom_key or "no-key",
            model=custom_model,
            base_url=custom_url,
            vendor=custom_vendor,
        )
    elif adapter_type == "ollama":
        from app.core.config import settings
        print("[ADAPTER FACTORY] -> Creating Ollama Adapter")
        return OllamaAdapter(
            base_url=settings.OLLAMA_BASE_URL,
            model=model_config.get("model", "llama3")
        )
    else:
        # Default to OpenAI
        from .openai_adapter import OpenAIAdapter
        from app.core.config import settings
        print(f"[ADAPTER FACTORY] -> Unknown adapter '{adapter_type}', defaulting to OpenAI")
        return OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY or "demo-key",
            model="gpt-4"
        )
