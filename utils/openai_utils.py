import logging
import os
import base64
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY topilmadi! AI funksiyalari ishlamaydi.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = (
    "Sen SmartAI — kuchli va aqlli AI assistantsan. "
    "Foydalanuvchiga doimo u yozgan tilda javob ber."
)


async def get_chat_response(messages: list) -> str:
    if not client:
        return "⚠️ OpenAI kaliti sozlanmagan."
    try:
        response = await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=2000,
            timeout=60,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI chat xatosi: {e}")
        return f"⚠️ OpenAI xatosi: {e}"


async def generate_image(prompt: str) -> str:
    if not client:
        raise RuntimeError("OPENAI_API_KEY sozlanmagan.")
    response = await client.images.generate(
        model=IMAGE_MODEL, prompt=prompt, n=1, size="1024x1024"
    )
    return response.data[0].url


async def analyze_image_and_chat(prompt: str, image_bytes: bytes) -> str:
    if not client:
        return "⚠️ OpenAI kaliti sozlanmagan."
    try:
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        response = await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or "Bu rasmni tahlil qil va batafsil tushuntir."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI vision xatosi: {e}")
        return f"⚠️ Rasm tahlilida xato: {e}"


async def transcribe_audio(file_path: str) -> str:
    if not client:
        return ""
    try:
        with open(file_path, "rb") as f:
            ts = await client.audio.transcriptions.create(model=WHISPER_MODEL, file=f)
            return ts.text or ""
    except Exception as e:
        logger.error(f"Whisper xatosi: {e}")
        return ""


async def analyze_document(text: str, query: str) -> str:
    return await get_chat_response([
        {"role": "user", "content": f"Hujjat:\n{text[:8000]}\n\nSavol: {query}"}
    ])
