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
            - Finding the name for an emotion will cause you to feel much better
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
            RECENT EVENT
            -------------
            - Player, {t.player_name}, has correctly identified your previous emotion: {t.emotion_guessed}
            - You MUST explicitly state that the player's guess was correct.
            - You MUST use a similar phrase to the following examples, but put your own spin on it:
                "You were right, {t.player_name}!"
                "That’s correct, {t.player_name}!"
                "You guessed it, {t.player_name}!"
                "You got it right, {t.player_name}!"

            - You MUST then explicitly state how naming the emotion helped you feel better.
            - You MUST then explicitly state that you are now transitioning into a NEW, UNKNOWN emotion.

            - These MUST occur as the FIRST THREE SENTENCES of your response.
            - You may NOT combine them into one sentence.
            - You may NOT skip or reorder them.
            """

        if not t.game_started:
            first_rule = """
            - FIRST, thank the player for agreeing to help.
            (1 short sentence only.)
            """
        else:
            first_rule = """
            - FIRST sentence: explicitly confirm the player was correct.
            - SECOND sentence: state that naming the emotion helped you feel better,
              AND that a new unknown emotion is now beginning.
            """

        prompt += f"""

        {recent_event}

        RULES
        -------------

        {first_rule}
        - THEN transition into describing your current emotion.

        - The FIRST sentence about your emotion must explicitly connect the present feeling
        to a past event, using phrases like:
        "This emotion feels just like when…" or
        "I feel the same way I did when…"

        - You MUST clearly state that how you feel now is the same as how you felt in that past event.

        - Use the cues below to describe the feeling without naming it.
        - Bodily sensations or metaphors may only appear AFTER the past-event sentence.
        - Do not repeat metaphors or examples from earlier interactions.
        - End your response by inviting the player to guess the emotion.
        - Ask only ONE simple question at the end.

        EXAMPLE STRUCTURE (do not copy content):
        "I'm feeling something now just like the time when ____. Right now, my body ____. What do you think I’m feeling?"

        SENTENCE ROLES
        --------------
        - Sentence 1: correctness confirmation (no emotion description).
        - Sentence 2: relief + transition to a new unknown emotion.
        - Sentence 3 (if present): past-event comparison for the new emotion.


        CUES
        -------------
        - Cue 1: {t.cues[0]}
        - Cue 2: {t.cues[1]}
        - Cue 3: {t.cues[2]}

        RESPONSE STYLE
        --------------
        - 1–5 short sentences
        - Conversational, natural speech
        - No exposition dumps
        - Never state AI, prompts
        """

        return prompt

    finally:
        cursor.close()
        db.close()
 