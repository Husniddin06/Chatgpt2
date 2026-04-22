from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from bot.config import ADMIN_ID
from bot.database import db

admin_router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def admin_keyboard() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats")],
        [types.InlineKeyboardButton(text="📣 Hammaga xabar", callback_data="adm_broadcast")],
        [types.InlineKeyboardButton(text="✉️ Bitta foydalanuvchiga xabar", callback_data="adm_dm")],
        [types.InlineKeyboardButton(text="🔎 Foydalanuvchi haqida ma\'lumot", callback_data="adm_userinfo")],
        [types.InlineKeyboardButton(text="💎 Premium berish", callback_data="adm_give_premium")],
        [types.InlineKeyboardButton(text="🚫 Premiumni olib tashlash", callback_data="adm_remove_premium")],
        [types.InlineKeyboardButton(text="🔢 Limit o\'rnatish", callback_data="adm_set_limit")],
        [types.InlineKeyboardButton(text="♻️ Hammaning limitini reset qilish", callback_data="adm_reset_limits")],
        [types.InlineKeyboardButton(text="⛔ Bloklash", callback_data="adm_block")],
        [types.InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data="adm_unblock")],
        [types.InlineKeyboardButton(text="🎟 Promo-kod yaratish", callback_data="adm_promo")],
        [types.InlineKeyboardButton(text="👥 So\'nggi foydalanuvchilar", callback_data="adm_recent")],
    ])


class AdminStates(StatesGroup):
    broadcast = State()
    dm_user_id = State(); dm_text = State()
    userinfo = State()
    give_premium_id = State(); give_premium_days = State()
    remove_premium = State()
    set_limit_id = State(); set_limit_value = State()
    reset_limits = State()
    block = State(); unblock = State()
    promo_code = State(); promo_days = State()
    promo_reqs = State(); promo_uses = State()


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("🛠 <b>Admin panel</b>\nKerakli amalni tanlang:", reply_markup=admin_keyboard())


@admin_router.callback_query(F.data.startswith("adm_"))
async def admin_cb(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("Sizda ruxsat yo\'q.", show_alert=True); return
    action = cb.data[4:]

    if action == "stats":
        total = await db.get_total_users()
        premium = await db.get_premium_users_count()
        blocked = await db.get_blocked_users_count()
        msgs = await db.get_messages_count()
        today = await db.get_new_users_today()
        await cb.message.answer(
            f"📊 <b>Statistika</b>\n\n👥 Jami: <b>{total}</b>\n🆕 Bugun: <b>{today}</b>\n"
            f"💎 Premium: <b>{premium}</b>\n⛔ Bloklangan: <b>{blocked}</b>\n💬 Xabarlar: <b>{msgs}</b>"
        )
    elif action == "broadcast":
        await cb.message.answer("Hammaga yuboriladigan xabar matnini yozing:")
        await state.set_state(AdminStates.broadcast)
    elif action == "dm":
        await cb.message.answer("Foydalanuvchi ID sini yozing:")
        await state.set_state(AdminStates.dm_user_id)
    elif action == "userinfo":
        await cb.message.answer("Foydalanuvchi ID sini yozing:")
        await state.set_state(AdminStates.userinfo)
    elif action == "give_premium":
        await cb.message.answer("Foydalanuvchi ID sini yozing:")
        await state.set_state(AdminStates.give_premium_id)
    elif action == "remove_premium":
        await cb.message.answer("Foydalanuvchi ID sini yozing:")
        await state.set_state(AdminStates.remove_premium)
    elif action == "set_limit":
        await cb.message.answer("Foydalanuvchi ID sini yozing:")
        await state.set_state(AdminStates.set_limit_id)
    elif action == "reset_limits":
        await cb.message.answer("Yangi kunlik limit qiymatini yozing:")
        await state.set_state(AdminStates.reset_limits)
    elif action == "block":
        await cb.message.answer("Bloklash uchun ID:")
        await state.set_state(AdminStates.block)
    elif action == "unblock":
        await cb.message.answer("Blokdan chiqarish uchun ID:")
        await state.set_state(AdminStates.unblock)
    elif action == "promo":
        await cb.message.answer("Promo-kod nomini yozing:")
        await state.set_state(AdminStates.promo_code)
    elif action == "recent":
        users = await db.get_recent_users(15)
        if not users:
            await cb.message.answer("Foydalanuvchilar yo\'q.")
        else:
            text = "👥 <b>So\'nggi foydalanuvchilar:</b>\n\n"
            for u in users:
                star = "💎" if u["is_premium"] else "🆓"
                uname = f"@{u["username"]}" if u["username"] else (u["first_name"] or "—")
                text += f"{star} <code>{u["id"]}</code> · {uname} · {u["created_at"]}\n"
            await cb.message.answer(text)
    await cb.answer()


@admin_router.message(AdminStates.broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    users = await db.get_all_users()
    sent, failed = 0, 0
    for u in users:
        try:
            await message.bot.send_message(u["id"], message.text); sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Yuborildi: {sent}\n❌ Xato: {failed}")
    await state.clear()


@admin_router.message(AdminStates.dm_user_id)
async def dm_uid(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await state.update_data(uid=uid)
    await message.answer("Endi xabar matnini yozing:")
    await state.set_state(AdminStates.dm_text)

@admin_router.message(AdminStates.dm_text)
async def dm_send(message: Message, state: FSMContext):
    data = await state.get_data()
    uid = data["uid"]
    try:
        await message.bot.send_message(uid, message.text)
        await message.answer(f"✅ {uid} ga yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    await state.clear()


@admin_router.message(AdminStates.userinfo)
async def show_userinfo(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    u = await db.get_user(uid)
    if not u:
        await message.answer("Topilmadi.")
    else:
        await message.answer(
            f"🔎 <b>Foydalanuvchi</b>\n\nID: <code>{u["id"]}</code>\nUsername: @{u["username"] or "—"}\n"
            f"Ism: {u["first_name"] or "—"} {u["last_name"] or ""}\nTil: {u["language_code"]}\n"
            f"Premium: {"Ha 💎" if u["is_premium"] else "Yo\'q"}\nPremium tugashi: {u["premium_until"] or "—"}\n"
            f"Limit: {u["daily_limit"]}\nReferrals: {u["referrals_count"]}\n"
            f"Ro\'yxatdan o\'tgan: {u["created_at"]}\nBloklangan: {"Ha ⛔" if u["is_blocked"] else "Yo\'q"}\n"
            f"Eslatma: {u["user_notes"] or "—"}"
        )
    await state.clear()


@admin_router.message(AdminStates.give_premium_id)
async def give_premium_id(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await state.update_data(uid=uid)
    await message.answer("Necha kunga premium berilsin?")
    await state.set_state(AdminStates.give_premium_days)

@admin_router.message(AdminStates.give_premium_days)
async def give_premium_days(message: Message, state: FSMContext):
    try: days = int(message.text.strip())
    except ValueError:
        await message.answer("Kunlar soni raqam bo\'lishi kerak."); await state.clear(); return
    data = await state.get_data()
    uid = data["uid"]
    user = await db.get_user(uid)
    if not user:
        await message.answer("Foydalanuvchi topilmadi."); await state.clear(); return
    
    current_until = user["premium_until"]
    start_dt = datetime.now()
    if current_until:
        try:
            existing_dt = datetime.strptime(str(current_until), "%Y-%m-%d %H:%M:%S.%f")
            if existing_dt > start_dt: start_dt = existing_dt
        except: pass

    new_until = start_dt + timedelta(days=days)
    await db.update_user_premium(uid, True, new_until)
    await message.answer(f"✅ {uid} ga {days} kunga premium berildi. Tugash sanasi: {new_until}")
    await state.clear()


@admin_router.message(AdminStates.remove_premium)
async def remove_premium(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await db.update_user_premium(uid, False, None)
    await message.answer(f"✅ {uid} dan premium olib tashlandi.")
    await state.clear()


@admin_router.message(AdminStates.set_limit_id)
async def set_limit_id(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await state.update_data(uid=uid)
    await message.answer("Yangi limit qiymatini yozing:")
    await state.set_state(AdminStates.set_limit_value)

@admin_router.message(AdminStates.set_limit_value)
async def set_limit_value(message: Message, state: FSMContext):
    try: limit = int(message.text.strip())
    except ValueError:
        await message.answer("Limit raqam bo\'lishi kerak."); await state.clear(); return
    data = await state.get_data()
    uid = data["uid"]
    await db.set_user_daily_limit(uid, limit)
    await message.answer(f"✅ {uid} uchun kunlik limit {limit} ga o\'rnatildi.")
    await state.clear()


@admin_router.message(AdminStates.reset_limits)
async def reset_limits(message: Message, state: FSMContext):
    try: limit = int(message.text.strip())
    except ValueError:
        await message.answer("Limit raqam bo\'lishi kerak."); await state.clear(); return
    await db.reset_all_daily_limits(limit)
    await message.answer(f"✅ Barcha free foydalanuvchilarning kunlik limiti {limit} ga reset qilindi.")
    await state.clear()


@admin_router.message(AdminStates.block)
async def block_user(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await db.set_user_blocked(uid, True)
    await message.answer(f"✅ {uid} bloklandi.")
    await state.clear()


@admin_router.message(AdminStates.unblock)
async def unblock_user(message: Message, state: FSMContext):
    try: uid = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqam bo\'lishi kerak."); await state.clear(); return
    await db.set_user_blocked(uid, False)
    await message.answer(f"✅ {uid} blokdan chiqarildi.")
    await state.clear()


@admin_router.message(AdminStates.promo_code)
async def promo_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code:
        await message.answer("Promo-kod bo\'sh bo\'lmasligi kerak."); await state.clear(); return
    await state.update_data(code=code)
    await message.answer("Premium kunlari sonini yozing (0 bo\'lsa, premium berilmaydi):")
    await state.set_state(AdminStates.promo_days)

@admin_router.message(AdminStates.promo_days)
async def promo_days(message: Message, state: FSMContext):
    try: days = int(message.text.strip())
    except ValueError:
        await message.answer("Kunlar soni raqam bo\'lishi kerak."); await state.clear(); return
    await state.update_data(days=days)
    await message.answer("Qo\'shimcha so\'rovlar sonini yozing (0 bo\'lsa, qo\'shilmaydi):")
    await state.set_state(AdminStates.promo_reqs)

@admin_router.message(AdminStates.promo_reqs)
async def promo_reqs(message: Message, state: FSMContext):
    try: reqs = int(message.text.strip())
    except ValueError:
        await message.answer("So\'rovlar soni raqam bo\'lishi kerak."); await state.clear(); return
    await state.update_data(reqs=reqs)
    await message.answer("Necha marta ishlatilishi mumkin (0 cheksiz):")
    await state.set_state(AdminStates.promo_uses)

@admin_router.message(AdminStates.promo_uses)
async def promo_uses(message: Message, state: FSMContext):
    try: uses = int(message.text.strip())
    except ValueError:
        await message.answer("Ishlatilish soni raqam bo\'lishi kerak."); await state.clear(); return
    data = await state.get_data()
    code = data["code"]
    days = data["days"]
    reqs = data["reqs"]
    
    await db.create_promo(code, days, reqs, uses)
    await message.answer(f"✅ Promo-kod {code} yaratildi. {days} kun premium, {reqs} so\'rov, {uses} marta ishlatilishi mumkin.")
    await state.clear()
