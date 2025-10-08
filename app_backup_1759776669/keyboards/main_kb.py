from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню для клиента
client_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💅 Записаться")],
        [KeyboardButton(text="🎁 Мои бонусы"), KeyboardButton(text="📅 Мои записи")],
    ],
    resize_keyboard=True
)

# Главное меню для мастера
master_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📆 Расписание")],
        [KeyboardButton(text="✅ Подтвердить записи"), KeyboardButton(text="❌ Отклонить записи")],
    ],
    resize_keyboard=True
)

