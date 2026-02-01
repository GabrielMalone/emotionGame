from dataclasses import dataclass
from typing import Optional, List

@dataclass
class EmotionGameTurn:
    idNPC: Optional[int] = None
    idUser: Optional[int] = None
    player_name: Optional[str] = None
    current_scene: Optional[str] = None
    voiceId: Optional[str] = None
    player_text: Optional[str] = None
    npc_memory: Optional[str] = None
    cues: Optional[List[str]] = None
    prompt: Optional[str] = None
    last_npc_text: Optional[str] = None
    turn_index: int = 0