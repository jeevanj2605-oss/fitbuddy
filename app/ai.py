import os
from google import genai

def _generate(prompt: str, model: str, fallback: str) -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return fallback + "\n\n(Set GOOGLE_API_KEY to enable Gemini-generated content.)"
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(model=model, contents=prompt)
        text = getattr(response, "text", None)
        return text.strip() if text else fallback
    except Exception:
        # Keep the app usable if the external AI service is temporarily unavailable.
        return fallback + "\n\n(Gemini is temporarily unavailable; this is a general sample.)"

def generate_workout_gemini(user):
    prompt = f"""Create a safe, approachable 7-day fitness plan in plain text.
User: {user.username}, age {user.age}, goal: {user.goal}, preferred intensity: {user.intensity}.
Include each day, warm-up (5-10 min), main activity with manageable sets/reps or duration,
and cooldown/recovery. Include rest/recovery days. Offer beginner-friendly alternatives.
Avoid extreme volume, weight-loss promises, calorie targets, or medical claims. Tell the user
to stop if they feel pain and consult a qualified adult/professional if unsure."""
    fallback = """DAY 1 — Full-body basics
Warm-up: Easy marching and shoulder circles, 5 minutes.
Main: Comfortable bodyweight squats, wall push-ups, and bird-dogs; 2 easy rounds.
Cooldown: Gentle stretching.

DAY 2 — Easy movement
Enjoy a walk, dance, or cycle at a comfortable pace for 15–25 minutes.

DAY 3 — Mobility
Try gentle hip, shoulder, and back mobility for 10–15 minutes.

DAY 4 — Strength practice
Repeat a few comfortable bodyweight movements from Day 1, keeping good form.

DAY 5 — Cardio choice
Choose an enjoyable, conversational-pace activity for 15–25 minutes.

DAY 6 — Recovery
Rest or take a relaxed walk and stretch gently.

DAY 7 — Rest and reflect
Take a rest day. Notice which activities felt comfortable and enjoyable."""
    return _generate(prompt, os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro"), fallback)

def generate_nutrition_tip_with_flash(goal):
    prompt = f"Give one concise, balanced, non-restrictive nutrition or recovery tip for the fitness goal: {goal}. No calorie limits or supplements."
    return _generate(prompt, os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash"),
                     "Build regular meals around a variety of foods, drink water throughout the day, and allow time for rest.")

def update_workout_plan(original, feedback, goal, intensity):
    prompt = f"""Revise this 7-day plan based on the user's feedback. Goal: {goal}; intensity preference: {intensity}.
Keep it balanced and safe, include recovery, and avoid extreme recommendations.
Original plan:\n{original}\n\nFeedback:\n{feedback}"""
    return _generate(prompt, os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro"),
                     original + "\n\nSuggested adjustment: incorporate the requested preference gradually and keep recovery days.")
