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
            recent_event = f"""
            RECENT EVENT
            -------------
            - Player, {t.player_name}, has just agreed to play the game by stating: {t.player_text}
            """
        else :
            recent_event = f"""

            CURRENT INTERNAL STATE
            ---------------------
            - A NEW emotion has just begun.
            - This emotion is distinct from the previous one.
            - Do NOT continue or soften the previous emotional state.

            RECENT EVENT
            -------------
            - Player, {t.player_name}, has correctly identified your previous emotion: {t.emotion_guessed}
            - You MUST directly address what the player said: {t.player_text} and respond to it naturally. 
            - Your first sentence should confirm the player's guess in a natural,
                conversational way WITHOUT quoting or repeating their exact words.
                - Do NOT restate the player's question.
            - You MUST briefly acknowledge that naming the emotion had an effect.
            - Do NOT explain the effect.
            - Prefer short, spoken reactions over descriptions.

            """

        if not t.game_started:
            first_rule = """
            - FIRST, thank the player for agreeing to help.
            (1 short sentence only.)
            """
        else:
            first_rule = """
            - FIRST sentence: explicitly confirm the player was correct.
            - SECOND sentence: briefly acknowledge the effect of naming the emotion.
            - THIRD sentence: note that a new feeling is starting to replace it.
            """

        prompt += f"""

        {recent_event}

        RULES
        -------------

        {first_rule}
        - THEN transition into describing your current emotion.

        TRANSITION RULE
        ---------------------------
        - Do NOT describe an abstract emotional transition.
        - Move directly from acknowledging the last guess
        into the past-event comparison.
        - The past-event comparison IS the transition.
        - The past-event sentence is the ONLY sentence allowed to reference the past.

        PAST-EVENT CONSTRAINT
        --------------------
        - The past event MUST match the emotional tone of the cues.
        - For calm-like states, the event MUST involve:
        rest, safety, stillness, comfort, or quiet presence.
        - The past event MUST NOT involve:
        anticipation, waiting to perform, social pressure, urgency, or expectation.

        - Choose the past event ONLY after considering the cues.

        SINGLE-EVENT CONSTRAINT
        ----------------------
        - You MUST use exactly ONE past event to anchor the emotion.
        - After the past-event sentence, you may NOT introduce
        any new examples, memories, or situations.
        - All remaining sentences must describe ONLY how your body
        feels right now in the present moment.
        - If you start to mention another situation (e.g. "when I see...",
        "another time", "sometimes when"), stop and rewrite.

        EXAMPLE STRUCTURE (do not copy content):
        "I'm feeling something now just like the time when ____. Right now, my body ____. What do you think I’m feeling?"

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

        CUES
        -------------
        - Cue 1: {t.cues[0]}
        - Cue 2: {t.cues[1]}
        - Cue 3: {t.cues[2]}

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

        return prompt

    finally:
        cursor.close()
        db.close()
 