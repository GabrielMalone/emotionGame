import os, uuid
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import base64
import hashlib

load_dotenv(".env")
AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
#------------------------------------------------------------------
# cache for 11 labs
#------------------------------------------------------------------
def tts_cache_key(text, voice_id, emotion):
    text = text.strip()
    raw = f"{voice_id}|{emotion}|{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
#------------------------------------------------------------------
# helper method
def saveAudio(audio):
    audio = b"".join(audio)
    audio_id = str(uuid.uuid4())
    path = f"{AUDIO_DIR}/{audio_id}.mp3"
    with open(path, "wb") as f:
        f.write(audio)
    return {"audio_id": audio_id}, 200
#------------------------------------------------------------------
def tts_cached(text, voice_id, emotion):
    key = tts_cache_key(text, voice_id, emotion)
    path = f"{AUDIO_DIR}/{key}.mp3"

    if os.path.exists(path):
        with open(path, "rb") as f:
            while True:
                chunk = f.read(32_768)  # 32KB
                if not chunk:
                    break
                print("USING CACHE!")
                yield chunk
        return

    audio_chunks = []
    for chunk in tts(text, voice_id, emotion):
        audio_chunks.append(chunk)
        yield chunk

    with open(path, "wb") as f:
        f.write(b"".join(audio_chunks))
# ----------------------------------------------------------------
# SPEECH TO TEXT (for human input)
# ----------------------------------------------------------------
def speech_to_text(wav_path: str) -> str:
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    with open(wav_path, "rb") as f:
        result = client.speech_to_text.convert(
            file=f,
            model_id="scribe_v2",   # ← correct param name
            language_code="eng",    # optional but recommended
        )
    return (result.text or "").strip()

# ----------------------------------------------------------------
# TEXT TO SPEECH (FOR NPC OUTPUT)
# ----------------------------------------------------------------
def tts(text, voice_id, emotion):

    print("\nTTS DEBUG: \n", voice_id)

    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    EMOTION_CUES = {
        # core
        "neutral": "",
        "calm": "",

        # positive
        "happy": "[happily] ",
        "excited": "[excitedly] ",

        # negative
        "sad": "[sadly, tears welling] ",
        "angry": "[angrily, blood boiling] ",
        "afraid": "[fearfully] ",
        "disgusted": "[disgusted, nauseous] ",
    }

    cue = EMOTION_CUES.get(emotion, "")
    tagged_text = f"{cue}{text.strip()}"

    try:
        audio = client.text_to_dialogue.convert(
            inputs=[
                {
                    "text": tagged_text,
                    "voice_id": voice_id,
                }
            ]
        )

        if isinstance(audio, (bytes, bytearray)):
            yield audio
        else:
            # some SDKs return iterable chunks even without stream=True
            yield b"".join(audio)

    except Exception as e:
        print("ERROR ElevenLabs TTS:", e)
        raise