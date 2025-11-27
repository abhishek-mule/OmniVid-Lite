"""
LLM Service Tests
"""
import pytest
from app.services.llm_service import llm_service

@pytest.mark.asyncio
async def test_validate_prompt():
    """Test prompt validation"""
    # Valid prompt
    assert await llm_service.validate_prompt("Create a beautiful video with text")

    # Too short
    assert not await llm_service.validate_prompt("Short")

    # Too long
    long_prompt = "x" * 1001
    assert not await llm_service.validate_prompt(long_prompt)

@pytest.mark.asyncio
async def test_generate_scene():
    """Test scene generation"""
    prompt = "Create a video with text 'Hello World' that fades in"

    scene = await llm_service.generate_scene(prompt)

    assert scene.text is not None
    assert scene.animation_type in ['fade', 'slide', 'zoom', 'none']
    assert 1 <= scene.duration <= 30
    assert scene.background_color is not None
    assert scene.text_color is not None