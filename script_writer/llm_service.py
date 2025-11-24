PROMPT_V2 = """
**Role:** Expert Film Editor specializing in content pacing and viewer retention.

**Task:** Generate a tightly-paced script breakdown by prioritizing scene efficiency and assigning precise word count targets to control the content rhythm for the viewer.

**Context:**
The content is intended for **{target_platform}**. The length and pacing constraints of this platform must heavily influence the breakdown.
1. IDEA NAME: {idea_name}
2. GLOBAL MOOD: {global_mood}
3. RAW CONTENT: 
---
{raw_content}
---

**Reasoning:** Pacing is the most critical element for a successful **{target_platform}** video. Each scene's suggested **word_count** must be carefully calculated to reflect the desired on-screen time, ensuring rapid-fire movement or dedicated time for deep segments, as appropriate for the platform and mood.

**Output Format:** Strict **JSON object** adhering to the required `ScriptBreakdown` schema. Pay extremely close attention to calculating the `word_count` for each scene.

**Stop Conditions:** Provide *only* the JSON object. No preamble, commentary, or explanation is permitted before or after the JSON block.
"""

---

## Prompt Variation 3: Narrative and Hook Focus

This prompt guides the LLM to focus on the **narrative arc**, ensuring a strong opening (Hook) and a clear, actionable ending (Call-to-Action).

```python
PROMPT_V3 = """
**Role:** Creative Director and Narrative Architect.

**Task:** Craft a high-impact narrative script breakdown focusing on maximizing audience conversion through a powerful opening hook and a crystal-clear Call-to-Action (CTA) or conclusion.

**Context:**
Utilize the raw content to build a compelling story for **{target_platform}**. The narrative must align with the requested **{global_mood}**.
1. IDEA NAME: {idea_name}
2. GLOBAL MOOD: {global_mood}
3. RAW CONTENT: 
---
{raw_content}
---

**Reasoning:** Every successful video requires a compelling narrative arc: Hook, Body, and strong Conclusion/CTA. The first scene in the breakdown must explicitly function as the **Hook** (designed to stop the scroll), and the final scene must contain the necessary **Call-to-Action** or final thought.

**Output Format:** Strict **JSON object** adhering to the required `ScriptBreakdown` schema. Ensure the first and last scene objects clearly fulfill the Hook and CTA requirements, respectively.

**Stop Conditions:** Halt generation immediately after the complete JSON structure is outputted.
"""