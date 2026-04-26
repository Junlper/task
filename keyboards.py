from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def menu_keyboard(lang='ru'):
    texts = {
        'ru': {'enemy': 'Создать противника', 'progress': 'Прогресс', 'settings': 'Настройки'},
        'en': {'enemy': 'Create Enemy', 'progress': 'Progress', 'settings': 'Settings'}
    }
    t = texts.get(lang, texts['ru'])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t['enemy'], callback_data="create_enemy"),
                InlineKeyboardButton(text=t['progress'], callback_data="progress")
            ],
            [
                InlineKeyboardButton(text=t['settings'], callback_data="settings")
            ]
        ]
    )


def settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="English", callback_data="lang_en")
            ]
        ]
    )