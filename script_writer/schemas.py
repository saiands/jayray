# script_writer/schemas.py
from pydantic import BaseModel, Field
from typing import List, Literal

class Scene(BaseModel):
    """Defines the structure for a single scene in the script breakdown."""
    scene_index: int = Field(description="The sequential number of the scene.")
    act_name: str = Field(description="A descriptive name for this act or segment (e.g., 'Introduction', 'Conflict', 'Resolution').")
    location_suggestion: str = Field(description="A brief suggestion for the setting or background (e.g., 'Open field at sunset', 'Cozy library').")
    action_summary: str = Field(description="A 1-2 sentence description of the action, visuals, and key dialogue in this scene.")
    est_sentence_count: int = Field(description="The estimated number of spoken sentences or lines for this scene to guide pacing.")
    local_mood: str = Field(description="The mood specific to this scene (e.g., 'Tense', 'Humorous', 'Reflective').")

class ScriptBreakdown(BaseModel):
    """The complete structured output for the LLM analysis."""
    global_mood: str = Field(description="The dominant, overarching mood for the entire piece, based on user input.")
    target_pacing: Literal["Fast", "Moderate", "Slow"] = Field(description="The recommended pace for the final delivery/edit.")
    scene_breakdown: List[Scene]