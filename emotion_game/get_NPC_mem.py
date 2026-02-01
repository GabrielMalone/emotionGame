import mysql.connector
import os
from turnContext import EmotionGameTurn
#---------------------------------------------------------------------------------
def connect()->object:
    return mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASSWORD'), 
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST', 'localhost') )
#---------------------------------------------------------------------------------
def getNPCmem(t : EmotionGameTurn):
    db = connect()
    if not db.is_connected():
        return
    try:
        cursor = db.cursor() 
        query = """
        SELECT
        kbText,
        updatedAt
        FROM npc_user_memory
        WHERE idNPC = %s
        AND idUser = %s;
        );
        """
        cursor.execute(query, (t.idNPC,t.idUser))
        row = cursor.fetchone()
        return row[0] if row else ""
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
    finally:
        cursor.close()
        db.close()  