from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    """Создает главное меню бота"""
    row1 = [
        KeyboardButton('👥 Игроки'),
        KeyboardButton('🗺️ Карты'),
        KeyboardButton('🏆 Турниры'),
        KeyboardButton('📈 Прогресс')
    ]
    row2 = [
        KeyboardButton('ℹ️ Аббревиатуры'),
        KeyboardButton('❓ Помощь')
    ]
    row3 = [
        KeyboardButton('🕓 История')
    ]
    row4 = [
        KeyboardButton('🔄 Перезапуск (/start)')
    ]
    keyboard = [row1, row2, row3, row4]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False, 
        input_field_placeholder="", 
        selective=False, 
        is_persistent=False
    )


def export_format_keyboard(callback_data):
    """Создает клавиатуру для выбора формата экспорта"""
    formats = [
        ('csv', '📄 CSV'),
        ('json', '🟫 JSON'),
        ('xlsx', '📊 Excel'),
        ('pdf', '📑 PDF')
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    for fmt, label in formats:
        keyboard.add(InlineKeyboardButton(
            text=label,
            callback_data=f"export_tablefmt_{callback_data}_{fmt}"
        ))
    cancel_cb = f'export_cancel_{callback_data}'
    keyboard.add(InlineKeyboardButton(text='❌ Отмена', callback_data=cancel_cb))
    return keyboard


def players_chart_keyboard():
    """Создает клавиатуру для выбора метрики диаграммы игроков"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    metrics = [
        ('rating', '⭐ Рейтинг'),
        ('adr', '💥 ADR'),
        ('kast', '🎯 KAST'),
        ('kd', '⚔️ K/D'),
        ('hs', '🎯 HS%'),
        ('opkd', '🚀 OpK-D')
    ]
    for m, label in metrics:
        keyboard.add(InlineKeyboardButton(text=label, callback_data=f"players_chart_{m}"))
    keyboard.add(InlineKeyboardButton(text='❌ Отмена', callback_data='players_chart_cancel'))
    return keyboard 