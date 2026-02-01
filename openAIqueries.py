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
    - Positive, supportive, or conversational replies alone are NOT agreement.
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
        model="gpt-4o-mini",
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

    print("\nCHILD GUESSED:", resp.choices[0].message.content)

    result = parse_llm_json(resp.choices[0].message.content)
    return result.get("guessed_emotion")
#------------------------------------------------------------------
def classify_emotion_guess_intent(t : EmotionGameTurn, client) -> bool:
    """
    Returns True if the player is attempting to identify or guess
    the NPC's emotional state. Otherwise False.
    """

    system = (
        "You classify player utterances in a children's emotion-learning game.\n"
        "Decide whether the player is attempting to identify or guess\n"
        "the NPC's emotion.\n\n"
        "Return ONLY valid JSON:\n"
        "{ \"is_guess\": true | false }\n\n"
        "Guidelines:\n"
        "- Greetings, small talk, questions like 'hello', 'how are you' are NOT guesses\n"
        "- Questions or statements naming or implying an emotion ARE guesses\n"
        "- Indirect guesses like 'you seem worried' count as guesses\n"
        "- Do not infer emotion correctness\n"
        "- Be conservative: only mark true if intent is clear"
    )

    user = f"""
    Player said:
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

    print("\nDID CHILD GUESS?:", resp.choices[0].message.content)

    result = parse_llm_json(resp.choices[0].message.content)
    return bool(result.get("is_guess", False))
#------------------------------------------------------------------

# ------------------------------------------------------------
# Hand-authored baseline cues (safe fallback)
# ------------------------------------------------------------
EMOTION_CUES = {
    "happy": [
        "my body feels bouncy, like I want to jump or dance",
        "like when you get good news or finish a fun game",
        "I keep smiling without trying and my voice sounds bright"
    ],
    "excited": [
        "my body feels wiggly, like it’s hard to stay still",
        "like waiting for a birthday or a surprise you really want",
        "my words want to come out fast and I feel extra energetic"
    ],
    "calm": [
        "my breathing feels slow and easy",
        "like sitting quietly or watching clouds move",
        "my body feels still and my voice sounds steady"
    ],
    "sad": [
        "my body feels heavy, like I want to sit or lie down",
        "like when something ends or you miss someone",
        "my voice feels softer and slower than usual"
    ],
    "afraid": [
        "my tummy feels tight and I want to stay very still",
        "like when the lights go out or you hear a loud noise at night",
        "my eyes keep looking around and my voice feels quiet"
    ],
    "angry": [
        "my body feels hot and tight, like my fists want to clench",
        "like when something feels really unfair or gets taken away",
        "my words want to come out fast and strong"
    ],
    "surprised": [
        "my body jumps a little, like I wasn’t ready for something",
        "like when someone suddenly says your name or pops out",
        "my eyes get wide and my breath catches for a moment"
    ],
    "disgusted": [
        "my body wants to pull away, like ‘yuck, no thank you’",
        "like smelling something really gross or touching slime you don’t like",
        "my face scrunches up and I want to move back"
    ],
}

# ------------------------------------------------------------
# Validation (tighten this over time)
# ------------------------------------------------------------
def validate_cues(cues: list[str], emotion: str) -> bool:
    if not isinstance(cues, list) or len(cues) != 3:
        return False

    banned = [
        "trauma", "death", "panic", "existential", "identity",
        "suicide", "kill", "blood"  # add more if you want
    ]

    e = emotion.lower().strip()

    for c in cues:
        if not isinstance(c, str):
            return False

        text = c.strip()
        if not text:
            return False

        # short, kid-friendly
        if len(text.split()) > 20:
            return False

        low = text.lower()

        # avoid unsafe topics
        if any(word in low for word in banned):
            return False

        # critical: don't leak the label
        if e in low:
            return False

    return True
# ------------------------------------------------------------
# OpenAI generator (returns list[str] or None)
# ------------------------------------------------------------
def generate_emotion_cues(emotion: str, client) -> list[str] | None:
    system = (
        "You generate short, child-friendly descriptions of emotions.\n"
        "Rules:\n"
        "- Audience is a child (ages 6–12)\n"
        "- Use concrete body sensations or everyday situations\n"
        "- No abstract psychology words\n"
        "- No adult topics, no threats, no violence\n"
        "- Do NOT name the emotion\n"
        "- Keep language simple and literal\n"
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
            model="gpt-4o-mini",
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