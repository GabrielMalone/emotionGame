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
def build_disagree_prompt(t : EmotionGameTurn) -> str:

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
        {t.npc_memorymem}

        RECENT EVENT
        -------------
        - Player, {t.player_name} ,has just disagreed to play the game by stating: {t.player_text}
    
        RULES
        -------------
        - Respond directly and appropriately to what the player said. 
        - Steer the conversation back to ghe game, but do so gently, and related back to what the player just said {t.player_text}.

        RESPONSE STYLE
        --------------
        - 1–2 short sentences
        - Conversational, natural speech
        - No exposition dumps
        """
        return prompt

    finally:
        cursor.close()
        db.close()
 