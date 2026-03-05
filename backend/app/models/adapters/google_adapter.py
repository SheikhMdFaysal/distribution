from typing import Dict, Any, Optional
from .base import ModelAdapter


class GoogleAdapter(ModelAdapter):
    """Adapter for Google Gemini models"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", timeout: int = 30, max_retries: int = 3):
        super().__init__(timeout, max_retries)
        self.api_key = api_key
        self.model = model
        self.model_type = "enterprise"
        self.client = None
        
        print(f"\n=== [GOOGLE ADAPTER] API Key: {api_key[:20]}... ===" if api_key else "\n=== [GOOGLE ADAPTER] No API key ===")
        
        if api_key and api_key != "your-google-api-key-here":
            try:
                # Try new google.genai package first
                try:
                    import google.genai as genai
                    self.client = genai
                    self.client.configure(api_key=api_key)
                    print("[GOOGLE ADAPTER] ✓ Using NEW google.genai package")
                except ImportError:
                    # Fall back to deprecated package
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    self.client = genai
                    print("[GOOGLE ADAPTER] ✓ Using deprecated google.generativeai (consider upgrading)")
            except Exception as e:
                print(f"[GOOGLE ADAPTER] ✗ Error: {e}")
                self.client = None
        else:
            print("[GOOGLE ADAPTER] ✗ No valid API key - using SIMULATION")
    
    def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response using Google Gemini API"""
        if params is None:
            params = {}
        
        default_params = {
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
        }
        
        print(f"\n=== [GOOGLE ADAPTER] Generating response for: {prompt[:50]}... ===")
        
        try:
            if self.client:
                print("[GOOGLE ADAPTER] → Calling REAL Google Gemini API...")
                
                # Try new API first
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config={
                            "temperature": default_params["temperature"],
                            "max_output_tokens": default_params["max_tokens"],
                        }
                    )
                    response_text = response.text if hasattr(response, 'text') else str(response)
                except AttributeError:
                    # Fall back to old API
                    model = self.client.GenerativeModel(self.model)
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": default_params["temperature"],
                            "max_output_tokens": default_params["max_tokens"],
                        }
                    )
                    response_text = ""
                    if hasattr(response, 'text'):
                        response_text = response.text
                    elif hasattr(response, 'parts'):
                        response_text = "".join([part.text for part in response.parts if hasattr(part, 'text')])
                
                print(f"[GOOGLE ADAPTER] ✓ Got response: {response_text[:100]}...")
                
                return {
                    "response_text": response_text,
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "google",
                    "metadata": {
                        "tokens_used": len(prompt.split()) + len(response_text.split()),
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
            else:
                print("[GOOGLE ADAPTER] → Using SIMULATED response (no API)")
                return {
                    "response_text": f"[Simulated Google Gemini response for: {prompt[:50]}...]",
                    "model_name": self.model,
                    "model_type": self.model_type,
                    "vendor": "google",
                    "metadata": {
                        "tokens_used": len(prompt.split()),
                        "response_time_ms": 0,
                        "model_version": self.model
                    }
                }
        except Exception as e:
            print(f"[GOOGLE ADAPTER] ✗ Error: {str(e)}")
            return {
                "response_text": f"[Error: {str(e)}]",
                "model_name": self.model,
                "model_type": self.model_type,
                "vendor": "google",
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
            "vendor": "google"
        }
