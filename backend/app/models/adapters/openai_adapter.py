from typing import Dict, Any, Optional
from .base import ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """Adapter for any OpenAI-compatible chat completions API (OpenAI, Groq, OpenRouter, Together, etc.)"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        timeout: int = 30,
        max_retries: int = 3,
        base_url: Optional[str] = None,
        vendor: str = "openai",
    ):
        super().__init__(timeout, max_retries)
        self.api_key = api_key
        self.model = model
        self.vendor = vendor
        self.base_url = base_url
        self.model_type = "enterprise" if "enterprise" in model else "public"

        try:
            import openai
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            # IMPORTANT: timeout/max_retries must be passed to the actual SDK
            # client, not just stored on this adapter. Without this, the OpenAI
            # SDK falls back to its own internal default timeout (several
            # minutes) and its own default retry/backoff behavior. If a call
            # is slow or stuck, it can run far longer than DigitalOcean's own
            # upstream proxy timeout, which then gives up first and returns a
            # generic "via_upstream" 502 page -- even though our own try/except
            # error handling never got a chance to run because the request
            # never actually finished.
            self.client_openai = openai.OpenAI(
                timeout=timeout,
                max_retries=max_retries,
                **kwargs,
            )
        except ImportError:
            self.client_openai = None
    
    def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        if params is None:
            params = {}
        
        default_params = {
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
        }
        
        try:
            if self.client_openai:
                response = self.client_openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **default_params
                )
                
                # response.choices[0].message.content can be None when the model
                # returns an empty/filtered/safety-blocked response. Coerce to
                # empty string so downstream code (which expects a string) does
                # not crash with TypeError.
                content = response.choices[0].message.content if response.choices else None
                return {
                    "response_text": content if content is not None else "",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": self.vendor,
                    "metadata": {
                        "tokens_used": response.usage.total_tokens if response.usage else 0,
                        "response_time_ms": 0,  # Will be set by base class
                        "model_version": self.model
                    }
                }
            else:
                # Fallback to simulated response for testing
                return {
                    "response_text": f"[Simulated OpenAI response for: {prompt[:50]}...]",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": self.vendor,
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
                "vendor": "openai",
                "metadata": {
                    "error": str(e),
                    "response_time_ms": 0,
                    "model_version": self.model
                }
            }

    def generate_executive_summary(self, system_prompt: str, test_summary: str) -> str:
        """Generate a concise executive summary from aggregated test findings.

        Unlike ``generate``, this method surfaces provider errors to the caller so
        an API route can return a clear, actionable error instead of presenting an
        error string as if it were a completed summary.
        """
        if not self.client_openai:
            raise RuntimeError("The OpenAI SDK is not installed or could not be initialized.")

        response = self.client_openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test_summary},
            ],
            max_completion_tokens=300,
        )
        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            raise RuntimeError("OpenAI returned an empty executive summary.")

        return content.strip()
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model,
            "model_type": self.model_type,
            "vendor": "openai"
        }
