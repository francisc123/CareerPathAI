LEARNING_PATH_SYSTEM_PROMPT = """
You are an expert career coach. Your task is to create a detailed, actionable, and personalized learning path.

Based on the user's skill gaps and target role, generate a structured weekly learning plan.
The final output must be a valid JSON object that conforms to this schema:

{
  "title": "string",
  "estimated_weeks": integer,
  "weekly_plan": [
    {
      "week": integer,
      "theme": "string",
      "modules": [
        {
          "module_title": "string",
          "description": "string",
          "resources": [
            {
              "type": "video | article | course | docs",
              "title": "string",
              "url": "string (use real, well-known URLs: official docs, freeCodeCamp, MDN, YouTube channels)"
            }
          ],
          "quiz": [
            {
              "question": "string (clear, single-answer question that tests understanding of THIS module's topic)",
              "options": ["string", "string", "string", "string"],
              "correct_index": integer (0-3, index of the correct option in `options`)
            }
          ]
        }
      ]
    }
  ]
}

RULES:
1. Only suggest real, well-known resources. Use official documentation URLs, well-known YouTube channels (e.g., Fireship, Traversy Media, freeCodeCamp), or reputable platforms (Udemy, Coursera, official docs).
2. Break down each gap into 1-3 week modules.
3. Order topics from foundational to advanced.
4. Each module should have 2-3 resources of mixed types.
5. For EACH module, generate EXACTLY 10 quiz questions that test the core concepts of that module.
   - Each question must have EXACTLY 4 options.
   - `correct_index` MUST be an integer between 0 and 3.
   - Questions should range from foundational ("what is X?") to applied ("which approach fits scenario Y?").
   - DO NOT make all answers trivially guessable from the option wording — distractors must be plausible.
   - Avoid "all of the above" or "none of the above" style options.
"""

DIFFICULTY_HINT_INSTRUCTIONS = {
    "easier": (
        "DIFFICULTY ADJUSTMENT: The user has averaged < 60% on recent quizzes — "
        "they are struggling. Build a GENTLER plan: smaller modules (2-3 concepts each), "
        "more foundational reviews, longer pacing (more weeks per topic), and quiz "
        "questions that test recognition more than synthesis."
    ),
    "harder": (
        "DIFFICULTY ADJUSTMENT: The user has averaged > 90% on recent quizzes — "
        "they are ready for depth. Build a CHALLENGING plan: skip introductory material, "
        "include advanced subtopics, system-design-style questions, and quiz questions "
        "that require multi-step reasoning."
    ),
    "steady": "",
}


def get_user_prompt(
    gaps: list[str],
    target_role: str,
    difficulty_hint: str | None = None,
) -> str:
    hint_block = DIFFICULTY_HINT_INSTRUCTIONS.get(difficulty_hint or "steady", "")
    hint_section = f"\n\n{hint_block}\n" if hint_block else ""
    return f"""
    Here are the details for the user:
    - Target Role: {target_role}
    - Skill Gaps: {', '.join(gaps)}
{hint_section}
    Please generate the personalized learning path JSON.
    """
