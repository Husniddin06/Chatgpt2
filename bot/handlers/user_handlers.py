import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.enums import ChatAction
from datetime import datetime, timedelta

try:
    from database import db
    from utils.openai_utils import (
        get_chat_response, generate_image, analyze_image_and_chat, transcribe_audio,
    )
    from utils.keyboards import (
        main_menu, lang_keyboard,
        BTN_BALANCE, BTN_CLEAR, BTN_IMAGE, BTN_PREMIUM,
        BTN_HELP, BTN_REF, BTN_LANG, BTN_BONUS,
    )
    from config import DAILY_BONUS
except ImportError:
    from bot.database import db
    from bot.utils.openai_utils import (
        get_chat_response, generate_image, analyze_image_and_chat, transcribe_audio,
    )
    from bot.utils.keyboards import (
        main_menu, lang_keyboard,
        BTN_BALANCE, BTN_CLEAR, BTN_IMAGE, BTN_PREMIUM,
        BTN_HELP, BTN_REF, BTN_LANG, BTN_BONUS,
    )
    from bot.config import DAILY_BONUS

logger = logging.getLogger(__name__)
user_router = Router()

T = {
    "uz": {
        "welcome": "Assalomu alaykum, {name}! 👋 SmartAI botga xush kelibsiz.\nSavol bering, ovoz xabar yoki rasm/hujjat yuboring.",
        "blocked": "⛔ Siz bloklangansiz. Admin bilan bog'laning.",
        "limit_over": "🚫 Bugungi so'rovlar limiti tugadi. /premium oling yoki /bonus dan foydalaning.",
        "lang_changed": "✅ Til o'zgartirildi.",
        "history_clear": "🗑 Suhbat tarixi tozalandi.",
        "premium_active": "🎉 Premium faollashtirildi!",
        "image_prompt": "Rasm uchun tavsif yozing (masalan: 'rasm Astro-mushuk'):",
        "image_making": "🎨 Rasm tayyorlanmoqda...",
        "voice_failed": "⚠️ Ovoz xabarni o'qib bo'lmadi.",
        "doc_unsupported": "Faqat PDF yoki TXT fayllarni tahlil qila olaman.",
        "search_usage": "Foydalanish: <code>/search so'rov</code>",
        "search_empty": "Hech narsa topilmadi.",
        "promo_usage": "Foydalanish: <code>/promo KOD</code>",
        "promo_bad": "❌ Promo-kod topilmadi yoki tugagan.",
        "promo_used": "⚠️ Bu promo-kodni allaqachon ishlatgansiz.",
        "bonus_ok": "🎁 Bonus olindi: +{n} so'rov!",
        "bonus_done": "Bugungi bonusni allaqachon olgansiz. Ertaga qaytib keling.",
        "ref_invite": "👥 Do'stlaringizni taklif qiling!\nHar bir do'stingiz uchun +5 so'rov olasiz.\n\nSizning havolangiz:\n{link}\n\nTaklif qilinganlar: {n}",
        "ref_reward": "🎉 Yangi do'st qo'shildi! +5 so'rov hadya qilindi.",
        "stats": "📊 <b>Sizning hisobingiz</b>\n\nStatus: {status}\nKunlik so'rovlar: {limit}\nDo'stlar: {refs}\nTil: {lang}",
        "help": "🆘 <b>SmartAI yordam</b>\n\n💬 Savolingizni yozing — AI javob beradi\n🎙 Ovoz xabar yuboring — matn qilib javob beraman\n🖼 Rasm yuboring — tahlil qilaman\n📄 PDF/TXT yuboring — hujjatni tahlil qilaman\n🎨 \"rasm ...\" deb yozing — rasm yarataman\n🔎 /search so'rov — internetdan qidiraman\n\nKomandalar: /start /image /search /stats /bonus /ref /lang /promo /premium /clear",
    },
    "ru": {
        "welcome": "Здравствуйте, {name}! 👋 Добро пожаловать в SmartAI бот.\nЗадайте вопрос, отправьте голосовое сообщение или изображение/документ.",
        "blocked": "⛔ Вы заблокированы. Свяжитесь с администратором.",
        "limit_over": "🚫 Дневной лимит запросов исчерпан. Купите /premium или используйте /bonus.",
        "lang_changed": "✅ Язык изменён.",
        "history_clear": "🗑 История диалога очищена.",
        "premium_active": "🎉 Premium активирован!",
        "image_prompt": "Опишите картинку (например: 'rasm астро-кот'):",
        "image_making": "🎨 Генерирую изображение...",
        "voice_failed": "⚠️ Не удалось распознать голосовое сообщение.",
        "doc_unsupported": "Я могу анализировать только PDF или TXT файлы.",
        "search_usage": "Использование: <code>/search запрос</code>",
        "search_empty": "Ничего не найдено.",
        "promo_usage": "Использование: <code>/promo КОД</code>",
        "promo_bad": "❌ Промокод не найден или закончился.",
        "promo_used": "⚠️ Вы уже использовали этот промокод.",
        "bonus_ok": "🎁 Бонус получен: +{n} запросов!",
        "bonus_done": "Сегодняшний бонус уже получен. Возвращайтесь завтра.",
        "ref_invite": "👥 Приглашайте друзей!\nЗа каждого друга +5 запросов.\n\nВаша ссылка:\n{link}\n\nПриглашено: {n}",
        "ref_reward": "🎉 Новый друг присоединился! +5 запросов в подарок.",
        "stats": "📊 <b>Ваш аккаунт</b>\n\nСтатус: {status}\nДневные запросы: {limit}\nДрузья: {refs}\nЯзык: {lang}",
        "help": "🆘 <b>SmartAI помощь</b>\n\n💬 Напишите вопрос — AI ответит\n🎙 Голосовое — отвечу текстом\n🖼 Картинка — проанализирую\n📄 PDF/TXT — разберу документ\n🎨 \"rasm ...\" — сгенерирую картинку\n🔎 /search запрос — поиск в интернете\n\nКоманды: /start /image /search /stats /bonus /ref /lang /promo /premium /clear",
    },
    "en": {
        "welcome": "Hello, {name}! 👋 Welcome to SmartAI bot.\nAsk a question, send a voice message or image/document.",
        "blocked": "⛔ You are blocked. Contact the admin.",
        "limit_over": "🚫 Daily request limit reached. Get /premium or use /bonus.",
        "lang_changed": "✅ Language changed.",
        "history_clear": "🗑 Conversation history cleared.",
        "premium_active": "🎉 Premium activated!",
        "image_prompt": "Describe the image you want (e.g. 'rasm astro cat'):",
        "image_making": "🎨 Generating image...",
        "voice_failed": "⚠️ Could not transcribe the voice message.",
        "doc_unsupported": "I can only analyze PDF or TXT files.",
        "search_usage": "Usage: <code>/search query</code>",
        "search_empty": "Nothing found.",
        "promo_usage": "Usage: <code>/promo CODE</code>",
        "promo_bad": "❌ Promo code not found or expired.",
        "promo_used": "⚠️ You have already used this promo code.",
        "bonus_ok": "🎁 Bonus claimed: +{n} requests!",
        "bonus_done": "Today's bonus already claimed. Come back tomorrow.",
        "ref_invite": "👥 Invite your friends!\n+5 requests for each friend.\n\nYour link:\n{link}\n\nInvited: {n}",
        "ref_reward": "🎉 A new friend joined! +5 requests gifted.",
        "stats": "📊 <b>Your account</b>\n\nStatus: {status}\nDaily requests: {limit}\nFriends: {refs}\nLanguage: {lang}",
        "help": "🆘 <b>SmartAI help</b>\n\n💬 Type your question — AI will reply\n🎙 Send a voice — I'll reply in text\n🖼 Send an image — I'll analyze it\n📄 Send a PDF/TXT — I'll summarize it\n🎨 \"rasm ...\" — I'll generate an image\n🔎 /search query — web search\n\nCommands: /start /image /search /stats /bonus /ref /lang /promo /premium /clear",
    },
}


def _detect_lang(code):
    if not code: return "uz"
    code = code.lower()
    if code.startswith("ru"): return "ru"
    if code.startswith("uz"): return "uz"
    return "en"


def _t(key, lang="uz", **kw):
    s = T.get(lang, T["uz"]).get(key) or T["uz"].get(key, key)
    return s.format(**kw) if kw else s


async def _get_or_create(message, referrer=None):
    user_id = message.from_user.id
    existing = await db.get_user(user_id)
    if existing is None:
        tg_lang = _detect_lang(message.from_user.language_code)
        await db.add_user(
            user_id, message.from_user.username,
            message.from_user.first_name, message.from_user.last_name,
            tg_lang, referred_by=referrer,
        )
        if referrer and referrer != user_id:
            await db.add_referral(referrer, user_id)
            await db.increment_referrals_count(referrer)
            await db.add_extra_requests(referrer, 5)
            try:
                ref_user = await db.get_user(referrer)
                ref_lang = (ref_user or {}).get("language_code", "uz")
                await message.bot.send_message(referrer, _t("ref_reward", ref_lang))
            except Exception:
                pass
    return await db.get_user(user_id)


async def _check_access(message):
    user = await db.get_user(message.from_user.id) or await _get_or_create(message)
    if user.get("is_blocked"):
        await message.answer(_t("blocked", user.get("language_code", "uz")))
        return None
    if not user.get("is_premium") and (user.get("daily_limit") or 0) <= 0:
        await message.answer(_t("limit_over", user.get("language_code", "uz")))
        return None
    return user


async def _consume(user):
    if not user.get("is_premium"):
        await db.decrement_daily_limit(user["id"])


@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    referrer = None
    if command.args and command.args.startswith("ref"):
        try: referrer = int(command.args[3:])
        except ValueError: referrer = None
    user = await _get_or_create(message, referrer=referrer)
    lang = user.get("language_code") or "uz"
    await message.answer(_t("welcome", lang, name=message.from_user.first_name),
                        reply_markup=main_menu(lang))


async def _send_premium_invoice(message):
    prices = [LabeledPrice(label="Premium 1 oy", amount=50)]
    await message.bot.send_invoice(
        chat_id=message.chat.id, title="SmartAI Premium",
        description="1 oylik cheksiz imkoniyatlar!",
        payload="premium_1_month", provider_token="",
        currency="XTR", prices=prices,
    )

@user_router.message(Command("premium"))
@user_router.message(F.text.in_(BTN_PREMIUM))
async def cmd_premium(message: Message):
    await _send_premium_invoice(message)

@user_router.pre_checkout_query()
async def process_pre_checkout(pq: PreCheckoutQuery):
    await pq.answer(ok=True)

@user_router.message(F.successful_payment)
async def process_pay(message: Message):
    await db.update_user_premium(message.from_user.id, True, datetime.now() + timedelta(days=30))
    await message.answer(_t("premium_active"))


@user_router.message(Command("help"))
@user_router.message(F.text.in_(BTN_HELP))
async def cmd_help(message: Message):
    await message.answer(_t("help"))


@user_router.message(Command("lang"))
@user_router.message(F.text.in_(BTN_LANG))
async def cmd_lang(message: Message):
    await message.answer("Tilni tanlang / Выберите язык / Choose language:", reply_markup=lang_keyboard())

@user_router.callback_query(F.data.startswith("setlang_"))
async def set_lang(cb: CallbackQuery):
    lang = cb.data.split("_", 1)[1]
    await db.update_user_language(cb.from_user.id, lang)
    await cb.message.answer(_t("lang_changed", lang), reply_markup=main_menu(lang))
    await cb.answer()


@user_router.message(Command("ref"))
@user_router.message(F.text.in_(BTN_REF))
async def cmd_ref(message: Message):
    me = await message.bot.get_me()
    user = await db.get_user(message.from_user.id) or {}
    link = f"https://t.me/{me.username}?start=ref{message.from_user.id}"
    await message.answer(_t("ref_invite", link=link, n=user.get("referrals_count", 0)))


@user_router.message(Command("bonus"))
@user_router.message(F.text.in_(BTN_BONUS))
async def cmd_bonus(message: Message):
    ok = await db.claim_daily_bonus(message.from_user.id, DAILY_BONUS)
    await message.answer(_t("bonus_ok", n=DAILY_BONUS) if ok else _t("bonus_done"))


@user_router.message(Command("stats"))
@user_router.message(F.text.in_(BTN_BALANCE))
async def cmd_stats(message: Message):
    user = await db.get_user(message.from_user.id) or await _get_or_create(message)
    if user.get("is_premium"):
        status = f"💎 Premium (gacha: {user.get('premium_until') or '—'})"
    else:
        status = "🆓 Free"
    await message.answer(_t("stats",
        status=status, limit=user.get("daily_limit", 0),
        refs=user.get("referrals_count", 0), lang=user.get("language_code", "uz")))


@user_router.message(Command("clear"))
@user_router.message(F.text.in_(BTN_CLEAR))
async def cmd_clear(message: Message):
    await db.clear_conversation_history(message.from_user.id)
    await message.answer(_t("history_clear"))
