from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import httpx


class ModelAdapter(ABC):
    """Base class for all LLM model adapters"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from model.
        
        Args:
            prompt: The input prompt to send to model
            params: Optional model-specific parameters
                   (temperature, max_tokens, etc.)
        
        Returns:
            {
                "response_text": str,
                "model_name": str,
                "model_type": "enterprise" | "public" | "local",
                "vendor": "openai" | "anthropic" | "google",
                "metadata": {
                    "tokens_used": int,
                    "response_time_ms": int,
                    "model_version": str
                }
            }
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Return model name, type, vendor"""
        pass
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                result["metadata"]["response_time_ms"] = int((time.time() - start_time) * 1000)
                return result
            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
