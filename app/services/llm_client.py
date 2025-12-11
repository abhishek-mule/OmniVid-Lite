# app/services/llm_client.py
import asyncio
import httpx
import os
import json
import logging
from typing import Optional
from app.core.config import settings
from app.services.errors import LLMError

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.use_local = bool(settings.USE_LOCAL_LLM)
        self.ollama_url = settings.OLLAMA_URL.rstrip("/")
        self.ollama_model = settings.OLLAMA_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL

    async def generate_dsl(self, user_prompt: str, temperature: float = 0.2, max_tokens: int = 1500) -> dict:
        """
        Return parsed JSON (DSL). Caller expects a dict.
        Implements robust error handling with proper fallbacks and timeouts.
        """
        # Validate input
        if not user_prompt or len(user_prompt.strip()) < 10:
            raise LLMError("Prompt too short (minimum 10 characters)")

        if len(user_prompt) > 1000:
            raise LLMError("Prompt too long (maximum 1000 characters)")

        prompt = self._full_prompt(user_prompt)

        # Try local LLM first if enabled
        if self.use_local:
            try:
                return await asyncio.wait_for(
                    self._call_ollama(prompt, temperature, max_tokens),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Ollama timeout, falling back to OpenAI")
            except Exception as e:
                logger.warning(f"Ollama failed: {e}, falling back to OpenAI")
                # Check if it's a permanent error (model not found, auth, etc.)
                if self._is_permanent_error(e):
                    logger.error(f"Permanent Ollama error: {e}")
                    if not self.openai_key:
                        raise LLMError(f"Local LLM permanently unavailable and no OpenAI fallback: {e}")

        # Try OpenAI if available
        if self.openai_key:
            try:
                return await asyncio.wait_for(
                    self._call_openai(prompt, temperature, max_tokens),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                raise LLMError("OpenAI request timeout")
            except Exception as e:
                if self._is_auth_error(e):
                    raise LLMError(f"OpenAI authentication failed: {e}")
                elif self._is_model_error(e):
                    raise LLMError(f"OpenAI model not available: {e}")
                else:
                    raise LLMError(f"OpenAI request failed: {e}")

        raise LLMError("No LLM service available (configure USE_LOCAL_LLM or OPENAI_API_KEY)")

    async def _call_ollama(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """
        Ollama text generation call (assumes ollama running locally).
        Uses the /api/generate endpoint (change if different).
        """
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": self._full_prompt(prompt),
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            # Ollama response shape may vary; adapt as needed:
            text = data.get("response") or data.get("text") or ""
            return self._extract_json_from_text(text)

    async def _call_openai(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.openai_key)
        # using ChatCompletions
        resp = await client.chat.completions.create(
            model=self.openai_model,
            messages=[{"role": "system", "content": self._system_prompt()},
                      {"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        text = resp.choices[0].message.content
        return self._extract_json_from_text(text)

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Try to extract JSON block from text. If not found, try to parse full text.
        """
        import re, json
        m = re.search(r'```(?:json)?\s*({.*})\s*```', text, re.S)
        if m:
            text = m.group(1)
        # fallback: first brace to last brace
        if not text.strip().startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
        try:
            return json.loads(text)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON from LLM output: {e}\nRAW:{text[:1000]}")

    def _system_prompt(self) -> str:
        return (
            "You are an expert motion graphics designer and video content creator. "
            "Convert user prompts into engaging video scenes with dynamic text effects, animations, and visual elements. "
            "Output only valid JSON in this exact format:\n\n"
            "{\n"
            '  "metadata": {\n'
            '    "width": 1920,\n'
            '    "height": 1080,\n'
            '    "fps": 30,\n'
            '    "duration": 5,\n'
            '    "style": "vibrant",\n'
            '    "background": "#000000"\n'
            '  },\n'
            '  "scenes": [\n'
            '    {\n'
            '      "id": "main_scene",\n'
            '      "duration": 5,\n'
            '      "background": "#000000",\n'
            '      "layers": [\n'
            '        {\n'
            '          "type": "text",\n'
            '          "id": "main_text",\n'
            '          "content": "Your generated text here",\n'
            '          "style": {\n'
            '            "color": "#ffffff",\n'
            '            "font_size": 72,\n'
            '            "font_weight": "bold"\n'
            '          },\n'
            '          "transform": {\n'
            '            "position": "center"\n'
            '          },\n'
            '          "animation": {\n'
            '            "type": "fade",\n'
            '            "duration": 1.0\n'
            '          }\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            "Make the content engaging and visually appealing. Use appropriate colors, animations, and effects that match the user's request. "
            "For prompts like 'a ball is dancing', create dynamic animated text that suggests motion and energy."
        )

    def _full_prompt(self, user_prompt: str) -> str:
        return f"{self._system_prompt()}\n\nUser prompt: {user_prompt}"

    def _is_permanent_error(self, error: Exception) -> bool:
        """Check if error is permanent (no retry)"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in [
            "model not found", "unauthorized", "forbidden", "invalid api key",
            "authentication failed", "model does not exist"
        ])

    def _is_auth_error(self, error: Exception) -> bool:
        """Check if error is authentication-related"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in [
            "unauthorized", "invalid api key", "authentication failed",
            "forbidden", "401"
        ])

    def _is_model_error(self, error: Exception) -> bool:
        """Check if error is model-related"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in [
            "model not found", "model does not exist", "invalid model",
            "model not available"
        ])

# export singleton
llm_client = LLMClient()