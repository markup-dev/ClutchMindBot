import io
import matplotlib.pyplot as plt
from tabulate import tabulate
from aiogram import types
from aiogram.types import InputFile
import json
import os
from config import FONT_PATH
from data_loader import (
    get_player_averages, get_player_stats, get_maps, get_map_stats,
    get_tournaments, get_match_by_index, get_best_map_for_player,
    get_last_match_for_player, get_players, get_match_list
)
from keyboards import main_menu, export_format_keyboard, players_chart_keyboard
from export_utils import export_data, HISTORY_PATH


def render_player_card(name, stats, with_keyboard=True):
    """Унификация вывода карточки игрока"""
    if not stats:
        return '❌ Игрок не найден.', None
    
    ratings = [float(s['Rating']) for s in stats]
    adrs = [float(s['ADR']) for s in stats]
    kasts = [float(s['KAST'].replace('%', '')) for s in stats if isinstance(s['KAST'], str)]
    avg_rating = sum(ratings) / len(ratings)
    avg_adr = sum(adrs) / len(adrs)
    avg_kast = sum(kasts) / len(kasts) if kasts else 0
    best_map = get_best_map_for_player(name)
    last_match = get_last_match_for_player(name)

    # Таблица средних значений
    table_data = [{
        "Рейтинг": f"{avg_rating:.2f}",
        "KAST": f"{avg_kast:.1f}%",
        "ADR": f"{avg_adr:.0f}",
        "K/D": f"{sum([float(s['K']) for s in stats]) / len(stats):.2f}/{sum([float(s['D']) for s in stats]) / len(stats):.2f}"
    }]
    table = tabulate(table_data, headers="keys", tablefmt="fancy_grid")

    text = (
        f"👤 <b>Профиль игрока: {name}</b>\n"
        f"🏆 <b>Команда: BakS eSports</b>\n\n"
        f"📊 <b>Средние показатели по всем матчам:</b>\n"
        f"<pre>{table}</pre>\n"
    )

    if best_map:
        text += f"🎯 <b>Лучшая карта:</b> <code>{best_map[0]}</code> (рейтинг <code>{best_map[1]:.2f}</code>)\n"

    if last_match:
        for p in last_match['overall']['players']['both']:
            if p['nickname'].lower() == name.lower():
                opponent = [t for t in last_match['teams'] if t != 'BAKS'][0]
                text += f"📅 <b>Последний матч:</b> vs <code>{opponent}</code>\n"
                text += f"⚔️ K/D: <code>{p['K']}K/{p['D']}D</code> | ⭐ Рейтинг: <code>{p['Rating']}</code> | 💥 ADR: <code>{p['ADR']}</code>\n"
                break

    text += f"\n🎮 <b>Выберите матч для подробной статистики:</b>"

    keyboard = None
    if with_keyboard:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(row_width=2)
        for idx, s in enumerate(stats):
            date = s['date']
            opponent = s.get('opponent', '-')
            button_text = f"{date} vs {opponent}"
            callback_data = f"player_match_{name}_{idx}"
            keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        keyboard.add(InlineKeyboardButton(text="⬅️ Назад к списку игроков", callback_data="back_players"))
        keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_player_{name}"))
    return text, keyboard


async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    text = (
        '🎮 <b>Добро пожаловать в аналитический бот <u>BakS eSports</u>!</b>\n\n'
        '📊 Я помогу вам анализировать статистику команды и игроков в удобном формате.\n\n'
        '🚀 <b>Что умеет бот:</b>\n'
        '• 📈 Подробная статистика игроков и матчей\n'
        '• 🗺️ Анализ по картам и турнирам\n'
        '• 📊 Построение графиков по любым метрикам\n'
        '• 🏆 Отслеживание прогресса команды\n'
        '• 📤 Экспорт данных в CSV, JSON, Excel, PDF — прямо из любого сообщения с таблицей!\n'
        '• 🕓 История ваших действий (просмотры, экспорты) — кнопка <b>🕓 История</b> в меню\n'
        '• ℹ️ Пояснения всех игровых терминов\n\n'
        '💡 <b>Как использовать:</b>\n'
        '• Нажимайте кнопки меню для быстрой навигации\n'
        '• Используйте команду <code>/help</code> для подробного списка функций\n'
        '• В списках доступны интерактивные кнопки для детального просмотра\n'
        '• Кнопка <b>📤 Экспорт</b> — для выгрузки данных в файлы (CSV, JSON, Excel, PDF)\n'
        '• Кнопка <b>🕓 История</b> — для просмотра последних действий\n\n'
        '🎯 <b>Готовы начать анализ?</b> Выберите раздел в меню ниже!'
    )
    await message.answer(text, reply_markup=main_menu())


async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        '📚 <b>Справочник по командам и функциям</b>\n\n'
        '🎮 <b>Основные команды:</b>\n'
        '• <code>/start</code> — главное меню и приветствие\n'
        '• <code>/players</code> — список всех игроков команды\n'
        '• <code>/player [ник]</code> — детальная статистика игрока\n'
        '• <code>/maps</code> — статистика по картам\n'
        '• <code>/tournaments</code> — матчи и турниры\n'
        '• <code>/progress</code> — динамика развития игроков\n'
        '• <code>/history</code> — <b>история ваших действий (просмотры, экспорты)</b>\n\n'
        '📊 <b>Аналитика и графики:</b>\n'
        '• <code>/graph [ник] [метрика]</code> — график по метрике игрока\n'
        '• Доступные метрики: Rating, ADR, KAST, K/D, HS%\n\n'
        '📤 <b>Экспорт данных:</b>\n'
        '• В каждом сообщении с таблицей есть кнопка <b>📤 Экспорт</b>\n'
        '• Поддерживаются форматы: CSV, JSON, Excel, PDF\n'
        '• Просто выберите нужный формат и скачайте файл!\n\n'
        '🕓 <b>История:</b>\n'
        '• Кнопка <b>🕓 История</b> в меню или команда <code>/history</code> — последние 10 действий\n\n'
        '🖱️ <b>Навигация:</b>\n'
        '• Используйте кнопки меню для быстрого доступа\n'
        '• В списках нажимайте на элементы для подробностей\n'
        '• В карточке игрока — кнопки для графиков по всем метрикам\n'
        '• Кнопка <b>📤 Экспорт</b> — выгрузка данных в CSV, JSON, Excel, PDF\n\n'
        '❓ <b>Нужна помощь?</b>\n'
        '• Кнопка <b>ℹ️ Аббревиатуры</b> — пояснения всех терминов\n'
        '• Кнопка <b>❓ Помощь</b> — этот справочник\n'
        '• <code>/feedback</code> — предложения и замечания\n\n'
        '🎯 <b>Примеры использования:</b>\n'
        '• <code>/player Due1yant</code> — статистика игрока Due1yant\n'
        '• <code>/graph Due1yant ADR</code> — график ADR игрока Due1yant\n'
        '• <code>/map Mirage</code> — статистика по карте Mirage'
    )
    await message.answer(help_text, reply_markup=main_menu())


async def cmd_abbr(message: types.Message):
    """Обработчик команды /abbr"""
    abbr_text = (
        '📚 <b>Справочник игровых терминов и аббревиатур</b>\n\n'
        '🎯 <b>Основные метрики:</b>\n'
        '• <b>K/D</b> — Kill/Death Ratio (соотношение убийств к смертям)\n'
        '• <b>ADR</b> — Average Damage per Round (средний урон за раунд)\n'
        '• <b>KAST</b> — Kills, Assists, Survived, Traded (% раундов с вкладом)\n'
        '• <b>Rating</b> — комплексная оценка эффективности игрока\n'
        '• <b>HS</b> — Headshot (процент убийств в голову)\n\n'
        '⚔️ <b>Дополнительные метрики:</b>\n'
        '• <b>OpK-D</b> — Opening Kill-Death (первые убийства/смерти)\n'
        '• <b>MKs</b> — Multi-Kills (множественные убийства за раунд)\n'
        '• <b>1vsX</b> — клатчи (победы в неравных ситуациях)\n'
        '• <b>A</b> — Assists (помощь в убийствах)\n'
        '• <b>A_f</b> — Flash Assists (помощь через ослепление)\n'
        '• <b>D_t</b> — Death Time (время до смерти)\n\n'
        '🗺️ <b>Карты и стороны:</b>\n'
        '• <b>T</b> — Terrorist (террористы)\n'
        '• <b>CT</b> — Counter-Terrorist (контр-террористы)\n'
        '• <b>MVP</b> — Most Valuable Player (самый ценный игрок)\n\n'
        '💡 <b>Совет:</b> Используйте эти термины для лучшего понимания статистики!'
    )
    await message.answer(abbr_text, reply_markup=main_menu())


async def cmd_players(message: types.Message):
    """Обработчик команды /players"""
    players_avg = get_player_averages()

    sorted_players = sorted(players_avg.items(), key=lambda x: x[1]['Rating'], reverse=True)

    table_data = []
    for i, (nickname, stats) in enumerate(sorted_players, 1):
        table_data.append({
            "Место": f"{i}",
            "Игрок": nickname,
            "Рейтинг": f"{stats['Rating']:.2f}",
            "ADR": f"{stats['ADR']:.0f}",
            "KAST": f"{stats['KAST']:.1f}%",
            "K/D": f"{stats['K']:.1f}/{stats['D']:.1f}"
        })

    table = tabulate(table_data, headers="keys", tablefmt="fancy_grid")

    description = (
        '👥 <b>Состав команды BakS eSports</b>\n\n'
        '📊 <b>Средние показатели по всем матчам:</b>\n'
        '• <b>Рейтинг</b> — комплексная оценка эффективности\n'
        '• <b>ADR</b> — средний урон за раунд\n'
        '• <b>KAST</b> — % раундов с вкладом в победу\n'
        '• <b>K/D</b> — соотношение убийств к смертям\n\n'
        '🎯 <b>Выберите игрока для подробной статистики:</b>'
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    for nickname, _ in sorted_players:
        keyboard.add(InlineKeyboardButton(text=nickname, callback_data=f"playerstat_{nickname}"))
    keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data="export_table_players"))
    keyboard.add(InlineKeyboardButton(text="📊 Диаграмма", callback_data="players_chart"))

    await message.answer(f'{description}\n<pre>{table}</pre>', reply_markup=keyboard)


async def cmd_maps(message: types.Message):
    """Обработчик команды /maps"""
    maps = get_maps()
    description = (
        '🗺️ <b>Карты в портфолио BakS eSports</b>\n\n'
        '📊 <b>Статистика по картам:</b>\n'
        'В таблице показано количество официальных матчей на каждой карте.\n\n'
        '🎯 <b>Для просмотра детальной статистики по карте:</b>\n'
        '• Выберите карту из списка ниже\n'
        '• Или используйте команду <code>/map [название]</code>\n'
        '• Пример: <code>/map Mirage</code>\n\n'
        '💡 <b>Подсказка:</b> Нажмите на карту для просмотра всех матчей на ней.'
    )
    table = tabulate(
        [{"Карта": name, "Матчей": len(maps[name])} for name in maps],
        headers="keys", tablefmt="fancy_grid"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    for name in maps:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"show_map_{name}"))
    keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data="export_table_maps"))
    await message.answer(f'{description}\n<pre>{table}</pre>', reply_markup=keyboard)


async def cmd_tournaments(message: types.Message):
    """Обработчик команды /tournaments"""
    tournaments = get_tournaments()
    text = (
        '🏆 <b>Турниры и матчи BakS eSports</b>\n\n'
        '📊 <b>История выступлений команды:</b>\n'
        'Ниже представлены все официальные турниры и матчи с подробной статистикой.\n\n'
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    match_idx = 1
    for t, games in tournaments.items():
        text += f"🏅 <b>{t}</b> (<code>{len(games)} матчей</code>):\n"
        for match in games:
            opp = [team for team in match['teams'] if team != 'BAKS'][0]
            text += f"   • <b>{match['date']}</b> vs <b>{opp}</b> — <code>{match['score']}</code>\n"
            keyboard.add(
                InlineKeyboardButton(
                    text=f"{match['date']} vs {opp}",
                    callback_data=f"match_{match_idx}"
                )
            )
            match_idx += 1
        text += "\n"
    # Кнопка экспорта: экспортировать список турниров
    keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data="export_table_tournaments"))
    text += '🎯 <b>Выберите матч для подробного анализа:</b>'
    await message.answer(text, reply_markup=keyboard)


async def cmd_progress(message: types.Message):
    """Обработчик команды /progress"""
    players = get_players()
    progress = []
    for player in players:
        stats = get_player_stats(player)
        if len(stats) >= 2:
            first = stats[0]['Rating']
            last = stats[-1]['Rating']
            arrow = '📈' if last > first else ('📉' if last < first else '➡️')
            progress.append((player, first, last, arrow))
    description = (
        '📈 <b>Динамика развития игроков BakS eSports</b>\n\n'
        '📊 <b>Анализ прогресса:</b>\n'
        'Показан рейтинг каждого игрока в первом и последнем матче.\n\n'
        '📈 <b>Индикаторы:</b>\n'
        '• 📈 — рейтинг вырос (положительная динамика)\n'
        '• 📉 — рейтинг снизился (требует внимания)\n'
        '• ➡️ — рейтинг стабилен (хорошая консистентность)\n\n'
        '💡 <b>Рейтинг</b> — комплексная оценка эффективности игрока за матч.\n\n'
        '🎯 <b>Результаты анализа:</b>'
    )
    lines = [f"👤 <b>{p}</b>: <code>{f:.2f}</code> → <code>{l:.2f}</code> {a}" for p, f, l, a in progress]
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="📊 Диаграмма", callback_data="progress_chart"))
    await message.answer(f'{description}\n' + '\n'.join(lines), parse_mode='HTML', reply_markup=keyboard)


async def cmd_player(message: types.Message):
    """Обработчик команды /player"""
    args = message.text.split()
    if len(args) == 2:
        name = args[1]
        stats = get_player_stats(name)
        text, keyboard = render_player_card(name, stats, with_keyboard=True)
        await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message.answer(
            '❓ <b>Как использовать команду:</b>\n\n'
            '📝 <code>/player [ник игрока]</code>\n\n'
            '🎯 <b>Примеры:</b>\n'
            '• <code>/player swetsi</code>\n'
            '• <code>/player player123</code>\n\n'
            '💡 <b>Совет:</b> Используйте кнопку "👥 Игроки" в меню для просмотра всех игроков команды.'
        )


async def cmd_map(message: types.Message):
    """Обработчик команды /map"""
    args = message.text.split() if message.text else []
    if len(args) == 2:
        name = args[1]
        stats = get_map_stats(name)
        if stats:
            table = tabulate(
                [{
                    "Дата": m.get("date", "-"),
                    "Соперник": m.get("opponent", "-"),
                    "Счёт": m.get("score", "-"),
                    "WinRate": "-"
                } for m in stats],
                headers="keys", tablefmt="fancy_grid"
            )
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_map_{name}"))
            await message.answer(
                f'🗺️ <b>Статистика по карте: {name.capitalize()}</b>\n\n'
                f'📊 <b>Все матчи BakS eSports на {name}:</b>\n'
                f'<pre>{table}</pre>\n\n'
                f'💡 <b>Совет:</b> Используйте кнопку "🗺️ Карты" в меню для просмотра всех карт.',
                reply_markup=keyboard
            )
        else:
            await message.answer(
                '❌ <b>Карта не найдена</b>\n\n'
                '🔍 <b>Возможные причины:</b>\n'
                '• Неправильное название карты\n'
                '• Карта не игралась в официальных матчах\n\n'
                '💡 <b>Решение:</b>\n'
                '• Проверьте правильность написания\n'
                '• Используйте кнопку "🗺️ Карты" в меню\n'
                '• Выберите карту из списка доступных'
            )
    else:
        await message.answer(
            '❓ <b>Как использовать команду:</b>\n\n'
            '📝 <code>/map [название карты]</code>\n\n'
            '🎯 <b>Примеры:</b>\n'
            '• <code>/map Mirage</code>\n'
            '• <code>/map Inferno</code>\n'
            '• <code>/map Dust2</code>\n\n'
            '💡 <b>Совет:</b> Используйте кнопку "🗺️ Карты" в меню для просмотра всех карт.'
        )


async def cmd_graph(message: types.Message):
    """Обработчик команды /graph"""
    args = message.text.split()
    if len(args) == 3:
        name, metric = args[1], args[2]
        stats = get_player_stats(name)
        if not stats:
            await message.answer('Игрок не найден.')
            return
        x = [s['date'] for s in stats]

        def parse_metric(val):
            if isinstance(val, str) and val.endswith('%'):
                return float(val.replace('%', ''))
            try:
                return float(val)
            except Exception:
                return 0

        y = [parse_metric(s[metric]) if metric in s else 0 for s in stats]
        plt.figure(figsize=(7, 4))
        plt.plot(x, y, marker='o')
        plt.title(f'{name} — {metric} по матчам')
        plt.xlabel('Дата')
        plt.ylabel(metric)
        plt.grid(True)
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await message.answer_photo(buf, caption=f'{name} — {metric} по матчам')
        plt.close()
    else:
        await message.answer('Используйте: /graph [ник] [метрика]')


async def cmd_alert(message: types.Message):
    """Обработчик команды /alert"""
    await message.answer(
        '🔔 <b>Система уведомлений</b>\n\n'
        '📱 <b>Функция в разработке</b>\n\n'
        '🚀 <b>Планируемые возможности:</b>\n'
        '• Уведомления о новых матчах\n'
        '• Алерты при достижении рекордов\n'
        '• Напоминания о турнирах\n'
        '• Персональные уведомления для игроков\n\n'
        '⏰ <b>Скоро будет доступно!</b>'
    )


async def cmd_history(message: types.Message):
    """Обработчик команды /history"""
    import json
    from export_utils import HISTORY_PATH
    user_id = message.from_user.id
    try:
        with open(HISTORY_PATH, encoding='utf-8') as f:
            history = json.load(f)
    except Exception:
        await message.answer('История пуста.')
        return
    user_history = [h for h in history if h.get('user_id') == user_id]
    if not user_history:
        await message.answer('История пуста.')
        return
    last = user_history[-10:][::-1]
    action_map = {
        'view_player_card': ('👤', 'Просмотр игрока'),
        'view_map': ('🗺️', 'Просмотр карты'),
        'view_match': ('🏆', 'Просмотр матча'),
        'export': ('📤', 'Экспорт'),
        'view_tournament': ('🏆', 'Просмотр турнира'),
        'view_progress': ('📈', 'Просмотр прогресса'),
        'view_players_chart': ('📊', 'Диаграмма игроков'),
        'view_abbr': ('ℹ️', 'Справка'),
    }
    lines = ["🕓 <b>Последние действия:</b>"]
    for h in last:
        ts = h.get('timestamp', '-')
        action = h.get('action', '-')
        emoji, label = action_map.get(action, ('❔', action))
        params = h.get('params', {})
        # Форматируем параметры
        if action == 'view_player_card':
            param_str = f"<b>{params.get('player','-')}</b>"
        elif action == 'view_map':
            param_str = f"<b>{params.get('map','-')}</b>"
        elif action == 'view_match':
            param_str = f"матч #{params.get('match_idx','-')}"
        elif action == 'export':
            param_str = f"<i>{params.get('type','-')}</i> → <code>{params.get('filename','')}</code> ({params.get('format','')})"
        elif action == 'view_tournament':
            param_str = f"<b>{params.get('tournament','-')}</b>"
        elif action == 'view_progress':
            param_str = f"<b>{params.get('player','-')}</b>"
        elif action == 'view_players_chart':
            param_str = f"<b>{params.get('metric','-')}</b>"
        elif action == 'view_abbr':
            param_str = ''
        else:
            param_str = str(params)
        lines.append(f"<b>{ts}</b> — {emoji} <b>{label}</b> {param_str}")
    text = '\n'.join(lines)
    await message.answer(text)


async def unknown(message: types.Message):
    """Обработчик неизвестных команд"""
    await message.answer(
        '❓ <b>Неизвестная команда</b>\n\n'
        '🔍 <b>Что делать:</b>\n'
        '• Используйте кнопки меню для навигации\n'
        '• Нажмите <b>❓ Помощь</b> для списка команд\n'
        '• Или команду <code>/help</code>\n\n'
        '💡 <b>Популярные команды:</b>\n'
        '• <code>/start</code> — главное меню\n'
        '• <code>/players</code> — список игроков\n'
        '• <code>/tournaments</code> — турниры\n'
        '• <code>/maps</code> — карты\n\n'
        '🎯 <b>Нужна помощь?</b> Нажмите кнопку "❓ Помощь" в меню!'
    ) 