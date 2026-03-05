from typing import Dict, Any, Optional
from .base import ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic Claude models"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", timeout: int = 30, max_retries: int = 3):
        super().__init__(timeout, max_retries)
        self.api_key = api_key
        self.model = model
        self.model_type = "enterprise" if "enterprise" in model else "public"
        
        try:
            import anthropic
            self.client_anthropic = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            self.client_anthropic = None
    
    def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response using Anthropic API"""
        if params is None:
            params = {}
        
        default_params = {
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
        }
        
        try:
            if self.client_anthropic:
                response = self.client_anthropic.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **default_params
                )
                
                return {
                    "response_text": response.content[0].text if response.content else "",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "anthropic",
                    "metadata": {
                        "tokens_used": response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
            else:
                # Fallback to simulated response
                return {
                    "response_text": f"[Simulated Anthropic response for: {prompt[:50]}...]",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "anthropic",
                    "metadata": {
                        "tokens_used": len(prompt.split()),
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
        except Exception as e:
            return {
                "response_text": f"[Error: {str(e)}]",
                "model_name": self.model,
                "model_type": self.model_type,
                "vendor": "anthropic",
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
            "vendor": "anthropic"
        }
