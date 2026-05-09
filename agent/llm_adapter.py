# agent/llm_adapter.py
import requests
import json
from typing import List, Dict, Optional, Generator

API_URL = "http://127.0.0.1:8080/v1"

class Qwen3Adapter:
    def __init__(self, model_path: str = "", n_ctx: int = 32768, enable_thinking: bool = True):
        self.n_ctx = n_ctx
        self.enable_thinking = enable_thinking
        self.api_key = "sk-llama.cpp"

    def toggle_thinking(self, enable: bool):
        self.enable_thinking = enable

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        **kwargs
    ) -> Generator[Dict, None, None]:
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # ← PARÁMETROS OFICIALES QWEN3-1.7B
        if self.enable_thinking:
            # MODO THINKING: Temperature=0.6, TopP=0.95, TopK=20 [[1]][[3]]
            sampling_params = {
                "temperature": 0.6,
                "top_p": 0.95,
                "top_k": 20,
                "min_p": 0.0,
                "presence_penalty": 1.5,
                "repeat_penalty": 1.1
            }
        else:
            # MODO NON-THINKING: Temperature=0.7, TopP=0.8, TopK=20 [[7]][[24]]
            sampling_params = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 20,
                "min_p": 0.0,
                "presence_penalty": 1.5,
                "repeat_penalty": 1.1
            }

        payload = {
            "model": "Qwen3-1.7B",
            "messages": messages,
            "stream": stream,
            **sampling_params
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = requests.post(
                f"{API_URL}/chat/completions",
                headers=headers,
                json=payload,
                stream=stream
            )
            response.raise_for_status()

            if stream:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith(' '):
                            data_str = decoded_line[len(' '):]
                            if data_str.strip() != '[DONE]':
                                yield json.loads(data_str)
            else:
                yield response.json()

        except Exception as e:
            yield {"choices": [{"message": {"content": f"Error conectando al servidor: {str(e)}"}}]}