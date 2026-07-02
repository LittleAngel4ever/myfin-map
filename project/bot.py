import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from update_data import get_back
from models_back import Link, Api_var

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "YOUR_TOKEN"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Машина состояний
class CurrencyState(StatesGroup):
    waiting_for_currency = State()

# === КЛАВИАТУРЫ ===

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основное меню"""
    kb = [
        [KeyboardButton(text="💱 Выбор валюты")],
        [KeyboardButton(text="ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_currency_keyboard() -> ReplyKeyboardMarkup:
    """Выбор валюты"""
    kb = [
        [KeyboardButton(text="🇺🇸 USD")],
        [KeyboardButton(text="🇪🇺 EUR")],
        [KeyboardButton(text="ru RUB")],
        [KeyboardButton(text="️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        "👋 <b>Добро пожаловать в Cource 24/7 Bot!</b>\n\n"
        "Вы попали в Telegram Bot о курсах валют 💱\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    """Информация о боте"""
    await message.answer(
        "🤖 <b>О боте</b>\n\n"
        "<b>Название:</b> Cource 24/7 Bot\n"
        "<b>Версия:</b> 1.0.0\n\n"
        "<b>Возможности:</b>\n"
        "• 📊 Актуальные курсы валют\n"
        "• 🏦 Топ лучших банков\n"
        "• 🗺️ Карта с отделениями\n"
        "• 🔄 Обновление в реальном времени\n\n"
        "<b>Разработчик:</b> @your_username\n\n"
        "Используйте кнопки для навигации 👇",
        parse_mode="HTML"
    )

@dp.message(F.text == "💱 Выбор валюты")
async def select_currency(message: Message, state: FSMContext):
    """Меню выбора валюты"""
    await state.set_state(CurrencyState.waiting_for_currency)
    await message.answer(
        "💱 <b>Выберите валюту:</b>\n\n"
        "Нажмите на кнопку с нужной валютой:",
        reply_markup=get_currency_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "️ Назад")
async def go_back(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "🔙 Возврат в главное меню",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text.in_(["🇺🇸 USD", "🇪🇺 EUR", "ru RUB"]))
async def show_currency_rates(message: Message, state: FSMContext):
    """Показ топ-5 банков для выбранной валюты"""
    currency_map = {
        "🇺🇸 USD": Link.USD,
        "🇪🇺 EUR": Link.EUR,
        "ru RUB": Link.RUB
    }
    
    selected_currency = currency_map.get(message.text)
    if not selected_currency:
        await message.answer("❌ Ошибка выбора валюты")
        return
    
    try:
        await message.answer("⏳ Загружаю актуальные курсы...")
        
        data = get_back(Api_var.BOT, selected_currency)
        buy_branches = data.get("buy", [])
        sell_branches = data.get("sell", [])
        
        logging.info(f"buy_branches count: {len(buy_branches)}")
        logging.info(f"sell_branches count: {len(sell_branches)}")
        
        if not buy_branches and not sell_branches:
            await message.answer("❌ Нет данных по этой валюте")
            return
        
        currency_name = message.text.split()[1] 
        target_currency = currency_name.lower() 
        
        logging.info(f"Ищем курсы для валюты: '{target_currency}'")
        
        text = f"🏆 <b>Топ-5 лучших курсов {currency_name}</b>\n\n"
        
        if buy_branches:
            text += "🟢 <b>ЛУЧШАЯ ПОКУПКА</b> (ниже курс - выгоднее):\n\n"
            for i, branch in enumerate(buy_branches[:5], 1):
                buy_rate = None
                
                for rate in branch.exchange_rates:
                    curr_from = str(getattr(rate.curr_from, 'value', rate.curr_from)).lower().strip()
                    curr_to = str(getattr(rate.curr_to, 'value', rate.curr_to)).lower().strip()
                    
                    if curr_from == target_currency and curr_to == "byn":
                        buy_rate = rate.rate
                        break

                    elif curr_from == "byn" and curr_to == target_currency:
                        buy_rate = rate.rate
                        break
                
                text += f"<b>{i}. {branch.bank_org.name}</b>\n"
                text += f"📍 {branch.address}\n"
                if buy_rate:
                    text += f"💵 Курс покупки: <b>{buy_rate}</b> BYN\n\n"
                else:
                    text += f"💵 Курс покупки: <b>не найден</b>\n\n"
        
        if sell_branches:
            text += "🔴 <b>ЛУЧШАЯ ПРОДАЖА</b> (выше курс - выгоднее):\n\n"
            for i, branch in enumerate(sell_branches[:5], 1):
                sell_rate = None
                
                for rate in branch.exchange_rates:
                    curr_from = str(getattr(rate.curr_from, 'value', rate.curr_from)).lower().strip()
                    curr_to = str(getattr(rate.curr_to, 'value', rate.curr_to)).lower().strip()
                    
                    if curr_from == "byn" and curr_to == target_currency:
                        sell_rate = rate.rate
                        break
                    elif curr_from == target_currency and curr_to == "byn":
                        sell_rate = rate.rate
                        break
                
                text += f"<b>{i}. {branch.bank_org.name}</b>\n"
                text += f"📍 {branch.address}\n"
                if sell_rate:
                    text += f"💸 Курс продажи: <b>{sell_rate}</b> BYN\n\n"
                else:
                    text += f"💸 Курс продажи: <b>не найден</b>\n\n"
        
        text += "✅ Актуально на сегодня"
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при получении данных. Попробуйте позже.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print(" Бот запущен и ждет команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
