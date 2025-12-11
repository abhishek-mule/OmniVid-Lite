"""
Scene Templates for OmniVid-Lite
Predefined templates that users can select and customize
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class AnimationType(str, Enum):
    FADE_IN = "fade_in"
    WRITE = "write"
    APPEAR = "appear"
    SLIDE_IN = "slide_in"
    APPEAR_ONE_BY_ONE = "appear_one_by_one"


class SceneType(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    TEXT = "text"
    BULLETS = "bullets"
    IMAGE = "image"
    SIDE_BY_SIDE = "side_by_side"
    TIMELINE = "timeline"


class TemplateScene(BaseModel):
    type: SceneType
    content: str = ""
    items: List[str] = Field(default_factory=list)
    left: str = ""
    right: str = ""
    events: List[Dict[str, str]] = Field(default_factory=list)
    animation: AnimationType = AnimationType.FADE_IN
    duration: float = Field(gt=0, le=30, default=3.0)


class VideoTemplate(BaseModel):
    id: str
    name: str
    description: str
    duration: float = Field(gt=0, le=300)
    scenes: List[TemplateScene]
    preview: str = ""  # Emoji or icon
    category: str = "general"


# Predefined templates
SCENE_TEMPLATES: Dict[str, VideoTemplate] = {
    "intro": VideoTemplate(
        id="intro",
        name="Intro Slide",
        description="Perfect opening with title and subtitle",
        duration=5.0,
        preview="📺",
        category="presentation",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{title}",
                animation=AnimationType.FADE_IN,
                duration=2.5
            ),
            TemplateScene(
                type=SceneType.SUBTITLE,
                content="{subtitle}",
                animation=AnimationType.WRITE,
                duration=2.5
            )
        ]
    ),

    "bullet_points": VideoTemplate(
        id="bullet_points",
        name="Bullet Points",
        description="Present key points with animated reveals",
        duration=8.0,
        preview="📋",
        category="presentation",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{title}",
                animation=AnimationType.FADE_IN,
                duration=2.0
            ),
            TemplateScene(
                type=SceneType.BULLETS,
                items=["{point1}", "{point2}", "{point3}"],
                animation=AnimationType.APPEAR_ONE_BY_ONE,
                duration=6.0
            )
        ]
    ),

    "comparison": VideoTemplate(
        id="comparison",
        name="Side-by-Side Comparison",
        description="Compare two options or concepts visually",
        duration=10.0,
        preview="⚖️",
        category="comparison",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{title}",
                animation=AnimationType.FADE_IN,
                duration=2.0
            ),
            TemplateScene(
                type=SceneType.SIDE_BY_SIDE,
                left="{left_content}",
                right="{right_content}",
                animation=AnimationType.SLIDE_IN,
                duration=8.0
            )
        ]
    ),

    "timeline": VideoTemplate(
        id="timeline",
        name="Timeline",
        description="Show chronological events or processes",
        duration=12.0,
        preview="📅",
        category="educational",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{title}",
                animation=AnimationType.FADE_IN,
                duration=2.0
            ),
            TemplateScene(
                type=SceneType.TIMELINE,
                events=[
                    {"time": "{time1}", "event": "{event1}"},
                    {"time": "{time2}", "event": "{event2}"},
                    {"time": "{time3}", "event": "{event3}"}
                ],
                animation=AnimationType.APPEAR_ONE_BY_ONE,
                duration=10.0
            )
        ]
    ),

    "how_it_works": VideoTemplate(
        id="how_it_works",
        name="How It Works",
        description="Step-by-step process explanation",
        duration=15.0,
        preview="🔄",
        category="educational",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{title}",
                animation=AnimationType.FADE_IN,
                duration=2.0
            ),
            TemplateScene(
                type=SceneType.TEXT,
                content="Step 1: {step1}",
                animation=AnimationType.SLIDE_IN,
                duration=3.0
            ),
            TemplateScene(
                type=SceneType.TEXT,
                content="Step 2: {step2}",
                animation=AnimationType.SLIDE_IN,
                duration=3.0
            ),
            TemplateScene(
                type=SceneType.TEXT,
                content="Step 3: {step3}",
                animation=AnimationType.SLIDE_IN,
                duration=3.0
            ),
            TemplateScene(
                type=SceneType.TEXT,
                content="Result: {result}",
                animation=AnimationType.FADE_IN,
                duration=4.0
            )
        ]
    ),

    "testimonial": VideoTemplate(
        id="testimonial",
        name="Customer Testimonial",
        description="Social proof with quote and attribution",
        duration=8.0,
        preview="💬",
        category="marketing",
        scenes=[
            TemplateScene(
                type=SceneType.TEXT,
                content="\"{quote}\"",
                animation=AnimationType.WRITE,
                duration=5.0
            ),
            TemplateScene(
                type=SceneType.SUBTITLE,
                content="- {name}, {title}",
                animation=AnimationType.FADE_IN,
                duration=3.0
            )
        ]
    ),

    "statistic": VideoTemplate(
        id="statistic",
        name="Key Statistic",
        description="Highlight important numbers or metrics",
        duration=6.0,
        preview="📊",
        category="marketing",
        scenes=[
            TemplateScene(
                type=SceneType.TITLE,
                content="{statistic}",
                animation=AnimationType.APPEAR,
                duration=3.0
            ),
            TemplateScene(
                type=SceneType.SUBTITLE,
                content="{context}",
                animation=AnimationType.FADE_IN,
                duration=3.0
            )
        ]
    )
}


def get_template(template_id: str) -> VideoTemplate:
    """Get a template by ID"""
    if template_id not in SCENE_TEMPLATES:
        raise ValueError(f"Template '{template_id}' not found")
    return SCENE_TEMPLATES[template_id]


def list_templates(category: str = None) -> List[VideoTemplate]:
    """List all available templates, optionally filtered by category"""
    templates = list(SCENE_TEMPLATES.values())
    if category:
        templates = [t for t in templates if t.category == category]
    return templates


def get_template_categories() -> List[str]:
    """Get list of available template categories"""
    return list(set(t.category for t in SCENE_TEMPLATES.values()))


def apply_template_variables(template: VideoTemplate, variables: Dict[str, str]) -> VideoTemplate:
    """
    Apply variables to a template (e.g., replace {title} with actual title)
    Returns a new template instance with variables substituted
    """
    import copy
    import re

    # Deep copy the template to avoid modifying the original
    customized = copy.deepcopy(template)

    # Function to replace variables in a string
    def replace_vars(text: str) -> str:
        if not text:
            return text
        for var, value in variables.items():
            text = text.replace(f"{{{var}}}", str(value))
        return text

    # Apply replacements to all scenes
    for scene in customized.scenes:
        scene.content = replace_vars(scene.content)
        scene.left = replace_vars(scene.left)
        scene.right = replace_vars(scene.right)

        # Replace in items list
        scene.items = [replace_vars(item) for item in scene.items]

        # Replace in events
        for event in scene.events:
            for key, value in event.items():
                event[key] = replace_vars(value)

    return customized


# Template suggestions based on prompt analysis
def suggest_templates_for_prompt(prompt: str) -> List[str]:
    """
    Analyze a prompt and suggest relevant templates
    Returns list of template IDs in order of relevance
    """
    prompt_lower = prompt.lower()

    suggestions = []

    # Timeline/process related
    if any(word in prompt_lower for word in ["timeline", "history", "process", "steps", "how to", "guide"]):
        suggestions.extend(["timeline", "how_it_works"])

    # Comparison related
    if any(word in prompt_lower for word in ["vs", "versus", "compare", "comparison", "difference", "better"]):
        suggestions.append("comparison")

    # Statistics/metrics
    if any(word in prompt_lower for word in ["statistic", "percent", "number", "metric", "data", "%"]):
        suggestions.append("statistic")

    # Testimonials/quotes
    if any(word in prompt_lower for word in ["testimonial", "quote", "said", "customer", "review"]):
        suggestions.append("testimonial")

    # Bullet points/lists
    if any(word in prompt_lower for word in ["points", "list", "features", "benefits", "reasons"]):
        suggestions.append("bullet_points")

    # Default to intro for general content
    if not suggestions:
        suggestions.append("intro")

    return suggestions[:3]  # Return top 3 suggestions