from flask import request, jsonify
import os
import mysql.connector
from datetime import datetime,timezone
from turnContext import EmotionGameTurn

#------------------------------------------------------------------
# will use this for KB datetime stamps
# entry = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Emory {kb_text}" 
#------------------------------------------------------------------

#------------------------------------------------------------------
def connect()->object:
    return mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASSWORD'), 
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST', 'localhost') )
#------------------------------------------------------------------
def mark_emotion_guessed_correct(t : EmotionGameTurn):
    db = connect()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE emotion_guess_game
        SET guessed_correctly = 1,
            completedAt = NOW()
        WHERE idUser = %s
          AND idNPC = %s
          AND idEmotion = %s;
    """, (t.idUser, t.idNPC, t.emotion_guessed_id))
    db.commit()
    cursor.close()
    db.close()
#------------------------------------------------------------------
def get_active_emotion(t : EmotionGameTurn) -> dict | None:
    db = connect()
    if not db.is_connected():
        return None

    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT e.idEmotion, e.emotion
            FROM emotion_guess_game g
            JOIN emotion e ON e.idEmotion = g.idEmotion
            WHERE g.idUser = %s
              AND g.idNPC = %s
              AND g.described = 1
              AND g.guessed_correctly = 0
            LIMIT 1;
        """
        cursor.execute(query, (t.idUser, t.idNPC))
        return cursor.fetchone()

    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        return None

    finally:
        cursor.close()
        db.close()
#------------------------------------------------------------------
def assign_next_emotion(t : EmotionGameTurn):

    db = connect()
    cursor = db.cursor(dictionary=True)

    # find unused emotion
    cursor.execute("""
        SELECT e.idEmotion, e.emotion
        FROM emotion e
        LEFT JOIN emotion_guess_game g
          ON g.idEmotion = e.idEmotion
         AND g.idUser = %s
         AND g.idNPC = %s
        WHERE g.idEmotion IS NULL
        LIMIT 1;
    """, (t.idUser, t.idNPC))

    emotion = cursor.fetchone()
    if not emotion:
        cursor.close()
        db.close()
        return None  # all emotions completed

    # assign it
    cursor.execute("""
        INSERT INTO emotion_guess_game
            (idUser, idNPC, idEmotion, described)
        VALUES (%s, %s, %s, 1);
    """, (t.idUser, t.idNPC, emotion["idEmotion"]))

    db.commit()
    cursor.close()
    db.close()
    return emotion

#------------------------------------------------------------------
def build_prompt(
    idNPC: int,
    idUser: int,
    pName: str,
    performed_emotion: dict | None,
    guessed_correctly: bool,
    player_made_guess: bool,
    first_interaction: bool,
    cues: list[str],
    player_text: str
) -> str:

    db = connect()
    cursor = db.cursor(dictionary=True)

    try:
        # --------------------------------------------------
        # NPC core
        # --------------------------------------------------
        cursor.execute("""
            SELECT n.nameFirst, n.age, n.gender,
                   p.role, p.personality_traits,
                   p.emotional_tendencies, p.speech_style,
                   p.moral_alignment,
                   b.BGcontent
            FROM NPC n
            LEFT JOIN npc_persona p ON p.idNPC = n.idNPC
            LEFT JOIN background b ON b.idNPC = n.idNPC
            WHERE n.idNPC = %s
        """, (idNPC,))
        npc = cursor.fetchone()

        # --------------------------------------------------
        # Relationship
        # --------------------------------------------------
        cursor.execute("""
            SELECT rt.typeRelationship, r.trust
            FROM playerNPCrelationship r
            JOIN relationshipType rt ON rt.idRelationshipType = r.idRelationshipType
            WHERE r.idNPC = %s AND r.idUser = %s
        """, (idNPC, idUser))
        rel = cursor.fetchone()

        prompt = f"""
            You are an NPC in a narrative game.

            Name: {npc['nameFirst']}
            Role: {npc['role']}
            Personality: {npc['personality_traits']}
            Speech style: {npc['speech_style']}

            BACKGROUND:
            {npc['BGcontent']}

            LATEST PLAYER MESSAGE:
            "{player_text}"
            """.strip()

        # --------------------------------------------------
        # FIRST INTERACTION
        # --------------------------------------------------
        if first_interaction:
            prompt += f"""

FIRST MEETING
-------------
This is your first interaction.

You must:
- Greet {pName}
- Introduce yourself as Emory
- Say you’ll act out a feeling
- Invite them to guess
- Begin expressing the feeling

Do NOT explain emotions.
Do NOT compare emotions.
Keep it warm and simple.
"""
            return prompt

        # --------------------------------------------------
        # NO ACTIVE EMOTION → NORMAL TALK
        # --------------------------------------------------
        if not performed_emotion:
            prompt += """
Respond naturally and socially.
Do not reference emotions unless the player does.
"""
            return prompt

        # --------------------------------------------------
        # PLAYER DID NOT GUESS
        # --------------------------------------------------
        if performed_emotion and not player_made_guess:
            prompt += f"""
EMOTIONAL SHARING (NO GUESS)
---------------------------
Respond directly to what the player said.

Then, optionally add ONE subtle detail showing how you feel physically
or what you notice right now.

Do NOT:
- Ask for a guess
- Teach emotions
- List cues

Possible inspiration (do not list):
- {cues[0]}
"""
            return prompt

        # --------------------------------------------------
        # PLAYER GUESSED INCORRECTLY
        # --------------------------------------------------
        if performed_emotion and player_made_guess and not guessed_correctly:
            prompt += f"""
INCORRECT GUESS RESPONSE
-----------------------
The player guessed, but it’s not correct.

You must:
- Acknowledge why the guess makes sense
- Say ONE similarity
- Say ONE difference using a kid-friendly example
- Invite another guess

Do NOT name the emotion.

You may draw from:
- {cues[0]}
- {cues[1]}
"""
            return prompt

        # --------------------------------------------------
        # PLAYER GUESSED CORRECTLY
        # --------------------------------------------------
        if performed_emotion and guessed_correctly:
            prompt += """
CORRECT GUESS
-------------
- Affirm warmly
- Name the emotion
- Say one short sentence about it

Do NOT introduce a new activity.
"""
            return prompt

        return prompt

    finally:
        cursor.close()
        db.close()