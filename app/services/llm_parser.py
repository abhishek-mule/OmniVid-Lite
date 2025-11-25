# app/services/llm_parser.py
import json, re
from typing import Optional
from openai import AsyncOpenAI
from ..core.config import settings

SYSTEM_PROMPT = """<PASTE the SYSTEM PROMPT EXACTLY from the DSL message you already have>"""

class LLMParser:
    def __init__(self, api_key: Optional[str]=None):
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            raise ValueError("OPENAI_API_KEY missing")
        # Check if using OpenRouter (key starts with sk-or- or model has /)
        if key.startswith("sk-or-") or "/" in (settings.OPENAI_MODEL or ""):
            self.client = AsyncOpenAI(
                api_key=key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = AsyncOpenAI(api_key=key)

    async def generate_dsl(self, user_prompt: str, temperature: float = 0.35, model: Optional[str] = None) -> dict:
        model = model or settings.OPENAI_MODEL
        res = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        raw = res.choices[0].message.content
        # Extract JSON robustly
        m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', raw, re.DOTALL)
        if m:
            raw = m.group(1)
        else:
            m2 = re.search(r'(\{.*\})', raw, re.DOTALL)
            if m2:
                raw = m2.group(1)
        return json.loads(raw)

# singleton
llm_parser = LLMParser()