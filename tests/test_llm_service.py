"""
LLM Service Tests
"""
import pytest
from app.services.llm_service import llm_service
from app.services.llm_client import llm_client
from app.schemas.scene_schema import DSLModel, SceneModel, TextLayer
from pydantic import ValidationError


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


class TestLLMClientValidation:
    """Test LLM client JSON schema validation and error handling"""

    def test_extract_json_from_text_valid(self):
        """Test extracting valid JSON from LLM text"""
        valid_json_text = '''Here is the scene configuration:
```json
{
  "meta": {
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "style": "cinematic"
  },
  "scenes": [
    {
      "id": "scene1",
      "duration": 150,
      "layers": [
        {
          "type": "text",
          "id": "text1",
          "content": "Hello World"
        }
      ]
    }
  ]
}
```
'''
        result = llm_client._extract_json_from_text(valid_json_text)
        assert isinstance(result, dict)
        assert "meta" in result
        assert "scenes" in result
        assert len(result["scenes"]) == 1

    def test_extract_json_from_text_invalid_json(self):
        """Test handling of invalid JSON from LLM"""
        invalid_json_text = "This is not JSON at all"

        with pytest.raises(ValueError, match="LLM output is not valid JSON"):
            llm_client._extract_json_from_text(invalid_json_text)

    def test_extract_json_from_text_schema_validation_failure(self):
        """Test fallback creation when schema validation fails"""
        # JSON that's valid JSON but doesn't match our schema
        invalid_schema_json = '''```json
{
  "invalid_field": "value",
  "missing_required_fields": true
}
```'''
        result = llm_client._extract_json_from_text(invalid_schema_json)

        # Should create a fallback DSL
        assert isinstance(result, dict)
        assert "meta" in result
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["layers"][0]["type"] == "text"

    def test_create_fallback_dsl(self):
        """Test fallback DSL creation from invalid input"""
        invalid_json = {"some_text": "Hello from invalid JSON"}

        result = llm_client._create_fallback_dsl(invalid_json)

        assert result is not None
        assert "meta" in result
        assert "scenes" in result
        assert len(result["scenes"]) == 1

        scene = result["scenes"][0]
        assert scene["id"] == "fallback_scene"
        assert len(scene["layers"]) == 1
        assert scene["layers"][0]["type"] == "text"
        assert "Hello from invalid JSON" in scene["layers"][0]["content"]

    def test_categorize_ai_error_temporary(self):
        """Test categorization of temporary AI errors"""
        from app.api.v1.endpoints.render import _categorize_ai_error

        temp_errors = [
            Exception("timeout"),
            Exception("connection refused"),
            Exception("rate limit exceeded"),
            Exception("service unavailable")
        ]

        for error in temp_errors:
            assert _categorize_ai_error(error) == "temporary"

    def test_categorize_ai_error_permanent(self):
        """Test categorization of permanent AI errors"""
        from app.api.v1.endpoints.render import _categorize_ai_error

        perm_errors = [
            Exception("authentication failed"),
            Exception("invalid api key"),
            Exception("model not found"),
            Exception("quota exceeded")
        ]

        for error in perm_errors:
            assert _categorize_ai_error(error) == "permanent"

    def test_categorize_ai_error_unknown(self):
        """Test categorization of unknown AI errors"""
        from app.api.v1.endpoints.render import _categorize_ai_error

        unknown_error = Exception("some random error")
        assert _categorize_ai_error(unknown_error) == "unknown"


class TestSceneSchemaValidation:
    """Test Pydantic scene schema validation"""

    def test_valid_dsl_model(self):
        """Test validation of a complete valid DSL"""
        valid_dsl = {
            "meta": {
                "fps": 30,
                "width": 1920,
                "height": 1080,
                "style": "cinematic"
            },
            "scenes": [
                {
                    "id": "scene1",
                    "duration": 150,
                    "layers": [
                        {
                            "type": "text",
                            "id": "text1",
                            "content": "Hello World",
                            "style": {"color": "#ffffff"}
                        }
                    ]
                }
            ]
        }

        dsl = DSLModel(**valid_dsl)
        assert dsl.meta.fps == 30
        assert len(dsl.scenes) == 1
        assert dsl.scenes[0].layers[0].content == "Hello World"

    def test_invalid_dsl_missing_scenes(self):
        """Test validation fails when scenes array is empty"""
        invalid_dsl = {
            "meta": {
                "fps": 30,
                "width": 1920,
                "height": 1080
            },
            "scenes": []  # Empty scenes array
        }

        with pytest.raises(ValidationError, match="must provide at least one scene"):
            DSLModel(**invalid_dsl)

    def test_invalid_layer_missing_required_fields(self):
        """Test validation fails when layer is missing required fields"""
        invalid_dsl = {
            "meta": {
                "fps": 30,
                "width": 1920,
                "height": 1080
            },
            "scenes": [
                {
                    "id": "scene1",
                    "duration": 150,
                    "layers": [
                        {
                            "type": "text",
                            "id": "text1"
                            # Missing required "content" field
                        }
                    ]
                }
            ]
        }

        with pytest.raises(ValidationError):
            DSLModel(**invalid_dsl)

    def test_text_layer_validation(self):
        """Test TextLayer model validation"""
        valid_text_layer = {
            "type": "text",
            "id": "text1",
            "content": "Hello World",
            "style": {"color": "#ffffff", "font_size": 48}
        }

        layer = TextLayer(**valid_text_layer)
        assert layer.type == "text"
        assert layer.content == "Hello World"
        assert layer.id == "text1"

    def test_scene_model_duration_validation(self):
        """Test SceneModel duration validation"""
        # Valid duration
        valid_scene = {
            "id": "scene1",
            "duration": 150,
            "layers": [{"type": "text", "id": "text1", "content": "test"}]
        }
        scene = SceneModel(**valid_scene)
        assert scene.duration == 150

        # Invalid duration (negative)
        invalid_scene = {
            "id": "scene1",
            "duration": -10,
            "layers": [{"type": "text", "id": "text1", "content": "test"}]
        }
        with pytest.raises(ValidationError):
            SceneModel(**invalid_scene)