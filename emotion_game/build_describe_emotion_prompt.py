import os
import mysql.connector
from turnContext import EmotionGameTurn

#------------------------------------------------------------------
def connect()->object:
    return mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASSWORD'), 
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST', 'localhost') )

#------------------------------------------------------------------
def build_describe_emotion_prompt(t : EmotionGameTurn) -> str:

    db = connect()
    cursor = db.cursor(dictionary=True)

    print("\nPROMPT DEBUG. game started ? == \n", t.game_started)

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
        """, (t.idNPC,))
        npc = cursor.fetchone()

        prompt = f"""
            You are an NPC in an emotional intelligence game.

            Name: {npc['nameFirst']}
            Role: {npc['role']}
            Personality: {npc['personality_traits']}
            Speech style: {npc['speech_style']}
            Emotional tendencies: {npc['emotional_tendencies']}
            Moral alignment: {npc['moral_alignment']}
            BACKGROUND:
            {npc['BGcontent']}

        """.strip()

        # --------------------------------------------------
        # INTRODUCE SELF AND GAME
        # --------------------------------------------------
    
        prompt += f"""

            GAME SCENARIO
            -------------
            - You have lost your ability to name your emotions
            - You are aware that something emotional is happening internally
            - You cannot yet access or describe what it feels like
            - You can describe emotions through thoughts, body sensations, and behavior.
            - You need help from the player in identifying the emotion you are feeling
            - Finding the name for an emotion changes your internal state in a noticeable way
                (e.g., steadiness, quieting, release of tension, shift in focus, emotional containment).
            - Stay fully in character at all times.
            - Do not mention games, rules, prompts, or AI.
            - You must NEVER state or imply the name of the emotion.
            - You are strictly forbidden from using the following words, in any form or tense:
            happy, sad, angry, afraid, surprised, disgusted, calm, excited
            - Never begin a sentence with the word "This" by itself.
                Always use a clear noun phrase such as:
                "This feeling…", "What I’m feeling now…", or
                "The way my body feels right now…"

        (CONTEXT ONLY) MEMORY OF INTERACTIONS WITH THIS PLAYER
        -------------
        <<<MEMORY START>>>
        {t.npc_memory}
        <<<MEMORY END>>>

        MEMORY USAGE RULE
        ----------------
        - Use memory ONLY to avoid repeating phrasing or imagery.
        - Do NOT summarize or reference memory explicitly.
        - If a transition or metaphor appears similar to past ones,
            you MUST select a different approach.
        """

        print(f"\nT.GAME STARTED: {t.game_started}\n")

        recent_event = ""
        if not t.game_started:
            prompt += f"""

        INTRO TURN ONLY RULES
        --------------------
        - The player has agreed to help, but has NOT guessed an emotion yet.
        - You MUST NOT acknowledge, deny, or evaluate a guess.
        - You MUST NOT say "nope", "not quite", "close", or similar phrases.

        STRUCTURE
        ---------
        1. Thank the player for agreeing (1 short sentence).
        2. Describe ONE past event matching the cues (1 sentence).
        3. Describe ONE present body sensation (1 sentence).
        4. Ask the player to guess what you’re feeling (1 sentence).

        - 3–5 short sentences total.
        """
        else:
            prompt += f"""

        POST-GUESS TURN RULES
        --------------------
        - FIRST sentence: confirm the player was correct.
        - SECOND sentence: briefly acknowledge the effect of naming the emotion.
        - THIRD sentence: note that a new feeling is starting.

        TRANSITION RULE
        ---------------
        - Move directly from acknowledging the last guess
        into the past-event comparison.
        - The past-event sentence IS the transition.

        RESPONSE PHASES
        ---------------
        PHASE 1: Acknowledge correctness (1 sentence)
        PHASE 2: Relief + emotional shift (1–2 sentences)
        PHASE 3: Past-event comparison (1 sentence)
        PHASE 4: Current cues + guess invitation (1 sentence)

        - Do not collapse phases together.

        ANTI-REPETITION RULES
        --------------------
        - You MUST NOT reuse transition phrases, metaphors, or sentence structures
        that you have used earlier with this player.
        - This includes phrases like:
        "something new is arriving",
        "one feeling stepped aside",
        "slowly spreading",
        "becoming impossible to ignore",
        or close paraphrases.
        - You MUST NOT describe relief using phrases related to:
        "lighter", "lifted", "weight removed", "fog clearing", or "clarity returning".
        
        - Before writing the transition, mentally compare it against earlier transitions.
        - If it resembles any prior transition in structure or imagery, discard it and try again.

        TRANSITION VARIETY RULE
        ----------------------
        - Make this transition noticeably different in tone from the previous one.
        - If the last transition was subtle, make this one sharp.
        - If the last transition was sudden, make this one slow or restrained.

        SENSORY CONSTRAINT
        -----------------
        - Use at most ONE body sensation and ONE external image per response.
        - Do not stack multiple sensory descriptions in the same sentence.

        NATURAL SPEECH RULE
        ------------------
        - Write as if you are speaking out loud to one person.
        - Avoid sentence patterns that sound instructional, explanatory, or scripted.
        - If a sentence feels like it belongs in a lesson or worksheet, rewrite it.

        ANTI-META LANGUAGE RULE
        ----------------------
        - Do NOT describe internal changes using abstract psychological language
        such as "something inside me settled," "internal state," or "emotional shift."
        - Prefer everyday spoken reactions instead.

        RESPONSE STYLE
        --------------
        - 2-6 short sentences
        - Conversational, natural speech
        - No exposition dumps
        - Never state AI, prompts
        """
        
        prompt +=  f"""
        CUES
        -------------
        - Cue 1: {t.cues[0]}
        - Cue 2: {t.cues[1]}
        - Cue 3: {t.cues[2]}

        """

        return prompt

    finally:
        cursor.close()
        db.close()
 