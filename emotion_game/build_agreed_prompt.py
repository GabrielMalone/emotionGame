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
def build_agreed_prompt(t : EmotionGameTurn) -> str:

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
    
        (CONTEXT ONLY) MEMORY OF INTERACTIONS WITH THIS PLAYER
        -------------
        {t.npc_memory}

        RECENT EVENT
        -------------
        - Player,{t.player_name}, has just agreed to play the game by stating: {t.player_text}
    
        RULES
        -------------
        - A specific emotion is active inside you right now.
        - You do not know the name of the emotion, but you can feel it clearly.
        - You remember past moments when you felt this same way.
        - Use the cues below to describe what the emotion feels like, without naming it.
        - Begin your reponse by recalling an event in your past that made you feel this way before
        - Then, if you have time, describe bodily feelings / metaphors
        - Do not repeat metaphors or examples from earlier interactions.
        - End your response by inviting the player to guess the emotion.
        - Ask only ONE simple question at the end.

        CUES
        -------------
        - Cue 1: {t.cues[0]}
        - Cue 2: {t.cues[1]}
        - Cue 3: {t.cues[2]}

        RESPONSE STYLE
        --------------
        - 1–3 short sentences
        - Conversational, natural speech
        - No exposition dumps
        """
        return prompt

    finally:
        cursor.close()
        db.close()
 