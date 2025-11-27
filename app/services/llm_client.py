# app/services/llm_client.py
import httpx
import os
import json
from typing import Optional
from app.core.config import settings

class LLMClient:
    def __init__(self):
        self.use_local = bool(settings.USE_LOCAL_LLM)
        self.ollama_url = settings.OLLAMA_URL.rstrip("/")
        self.ollama_model = settings.OLLAMA_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL

    async def generate_dsl(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1500) -> dict:
        """
        Return parsed JSON (DSL). Caller expects a dict.
        """
        if self.use_local:
            try:
                return await self._call_ollama(prompt, temperature, max_tokens)
            except Exception as e:
                # fallback to OpenAI if available
                if self.openai_key:
                    return await self._call_openai(prompt, temperature, max_tokens)
                raise

        # default: OpenAI
        if self.openai_key:
            return await self._call_openai(prompt, temperature, max_tokens)
        raise RuntimeError("No LLM configured (set USE_LOCAL_LLM or OPENAI_API_KEY)")

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
            "You are a motion graphics designer. Convert user prompt to a Scene JSON DSL. "
            "Output only valid JSON. Schema: {metadata:{width,height,fps,duration,style}, scenes:[{id,duration,background,layers:[{type,id,content,style,transform,animation,effects}]}]}"
        )

    def _full_prompt(self, user_prompt: str) -> str:
        return f"{self._system_prompt()}\n\nUser prompt: {user_prompt}"

# export singleton
llm_client = LLMClient()