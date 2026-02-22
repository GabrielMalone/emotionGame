from emotionGameQueries import *
import re
import json
from turnContext import EmotionGameTurn

#------------------------------------------------------------------
def getResponseStream(t: EmotionGameTurn, client):
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.85,
            top_p=0.9,
            stream=True, 
            messages=[
                {
                    "role": "system",
                    "content": t.prompt
                },
                {
                    "role": "system",
                    "content": f"""
                    CURRENT SCENE (STABLE CONTEXT – DO NOT REPEAT OR REFER TO DIRECTLY)
                    -------------
                    {t.current_scene}

                    PLAYER NAME
                    -----------
                    {t.player_name}
                    """
                }
            ],
        )

        full = []

        for chunk in response:
            delta = chunk.choices[0].delta

            if delta and delta.content:
                token = delta.content
                full.append(token)
                yield token
        return "".join(full)

    except Exception as e:
        print("ERROR:", e)

#------------------------------------------------------------------
def classify_player_response_to_game_start(t : EmotionGameTurn, client):
    """
    Returns True if the player agrees to help the NPC identify their emotions.
    """
    system = """
    You classify player responses in a children's emotion-learning game.

    Your task is to decide whether the player AGREES to help the NPC identify emotions.

    Return ONLY valid JSON:
    { "agrees_to_help": true | false }

    Core rule:
    - Short affirmations (e.g. "okay", "sure", "yeah") ONLY count as agreement
    if they are responding to a direct request from the NPC to help identify emotions.

    Rules:
    - TRUE only if the player agrees to participate in the task of identifying emotions.
    - Agreement may be explicit ("I can help", "let's do it")
    or implicit ("okay", "sure") IF the NPC just asked for help with emotions.
    - Replies that express willingness, openness, or interest
    (e.g. "sure", "sounds interesting", "okay", "I'm curious")
    COUNT as agreement IF the NPC just asked for help identifying emotions.
    - If the NPC's last statement was NOT a request to help with emotions,
    short affirmations do NOT count as agreement.
    - If unsure, return false.
    """

    user = f"""
    NPC's last statement (what the player is responding to):
    \"\"\"{t.last_npc_text}\"\"\"

    Context (for understanding only — do NOT classify this text):
    \"\"\"{t.npc_memory}\"\"\"

    Player replied:
    \"\"\"{t.player_text}\"\"\"
    """

    resp = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )

    print(f"\n PLAYER'S INPUT {t.player_text} MEANS DECIDED TO AGREE IS: {resp.choices[0].message.content}")

    result = parse_llm_json(resp.choices[0].message.content)
    return bool(result.get("agrees_to_help", False))  
#------------------------------------------------------------------
def classify_emotion_guess(t: EmotionGameTurn, client):
    system = (
        "You classify whether a child is attempting to identify an emotion.\n"
        "Map the player's input to ONE of the allowed emotions if applicable.\n"
        "If the player is not clearly guessing an emotion, return null.\n\n"
        "Allowed emotions:\n"
        "- happy\n"
        "- sad\n"
        "- angry\n"
        "- afraid\n"
        "- surpised\n"
        "- calm\n"
        "- excited\n"
        "- disgusted\n\n"
        "Return ONLY valid JSON:\n"
        "{ \"guessed_emotion\": string | null }\n"
        "Do not explain."
    )

    user = f"""
    Player input:
    \"\"\"{t.player_text}\"\"\"
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )

    result = parse_llm_json(resp.choices[0].message.content)
    return result.get("guessed_emotion")
# ------------------------------------------------------------
# OpenAI generator (returns list[str] or None)
def normalize_emotion(emotion) -> str:
    if isinstance(emotion, str):
        return emotion
    if isinstance(emotion, dict) and "emotion" in emotion:
        return emotion["emotion"]
    raise ValueError(f"Invalid emotion: {emotion!r}")
# ------------------------------------------------------------
def generate_emotion_cues(emotion: str, client) -> list[str] | None:

    emotion = normalize_emotion(emotion)
    print(f"DEBUGGING EMOTION SETTING {emotion}")

    system = (
        "You generate short,descriptions of emotions.\n"
        "Rules:\n"
        "- Use concrete body sensations or everyday situations\n"
        "- No abstract psychology words\n"
        "- Do NOT name the emotion\n"
        "- Return ONLY valid JSON\n"
    )

    user = f"""
        Generate 3 different clues for this emotion:

        Emotion: {emotion}

        Each clue must be:
        1) A body feeling OR
        2) A familiar kid experience OR
        3) A visible behavior

        Return JSON only in exactly this shape:
        {{"cues":["...","...","..."]}}
        """.strip()

    try:
        resp = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = parse_llm_json(resp.choices[0].message.content)
        return content["cues"]

    except Exception:
        # any parse / API / schema issue -> fallback
        return None
# ------------------------------------------------------------
# Single entry point you call from build_prompt()
# ------------------------------------------------------------
def get_cues_for_emotion(emotion: str, client) -> list[str]:
    """
    Always returns 3 child-friendly cues generated by OpenAI.
    Falls back to safe generic cues ONLY if generation fails.
    """

    try:
        cues = generate_emotion_cues(emotion, client)
        return cues

    except Exception as e:
        print(f"[CUE GEN FAILED] {emotion}: {e}")

    # absolute last-resort fallback (never emotion-specific)
    return [
        "my body feels different in a noticeable way",
        "it feels like something important is happening",
        "my face and voice change a little"
    ]

# ------------------------------------------------------------
def parse_llm_json(text: str) -> dict:
    """
    Robustly parse JSON returned by an LLM.
    Strips markdown fences and leading/trailing text.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # Remove ```json ``` or ``` fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Could not parse JSON from LLM output:\n{text}")