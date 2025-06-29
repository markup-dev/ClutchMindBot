import io
import matplotlib.pyplot as plt
from tabulate import tabulate
from aiogram import types
from aiogram.types import InputFile
import json
import os
from config import FONT_PATH
from export_utils import log_history

from data_loader import (
	get_player_averages, get_player_stats, get_maps, get_map_stats,
	get_tournaments, get_match_by_index, get_players
)
from handlers import render_player_card
from keyboards import export_format_keyboard, players_chart_keyboard


async def player_match_callback(call: types.CallbackQuery):
	"""Обработчик для показа матча игрока"""
	# player_match_{name}_{idx}
	parts = call.data.split('_', maxsplit=3)
	if len(parts) < 4:
		await call.message.edit_text('Матч не найден.')
		return
	_, _, name, idx = parts
	try:
		idx = int(idx)
	except Exception:
		await call.message.edit_text('Матч не найден.')
		return
	stats = get_player_stats(name)
	if not stats or idx < 0 or idx >= len(stats):
		await call.message.edit_text('Матч не найден.')
		return
	match_stat = stats[idx]
	table_data = [{
		"K": match_stat['K'],
		"D": match_stat['D'],
		"ADR": match_stat['ADR'],
		"KAST": match_stat['KAST'],
		"OpK-D": match_stat['OpK-D'],
		"MKs": match_stat['MKs'],
		"1vsX": match_stat['1vsX'],
		"HS": match_stat['HS'],
		"A": match_stat['A'],
		"A_f": match_stat['A_f'],
		"D_t": match_stat['D_t'],
		"Rating": match_stat['Rating']
	}]
	table = tabulate(table_data, headers="keys", tablefmt="fancy_grid")
	date = match_stat['date']
	opponent = match_stat.get('opponent', '-')
	text = (
		f"<b>Статистика игрока: {name} — матч {date} vs {opponent}</b>\n"
		f"<pre>{table}</pre>"
	)
	from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
	keyboard = InlineKeyboardMarkup(row_width=2)
	keyboard.add(InlineKeyboardButton(text="⬅️ Назад к игроку", callback_data=f"playerstat_{name}"))
	keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_player_match_{name}_{idx}"))
	# Компактные кнопки графиков по основным метрикам (по 2 в ряд)
	metrics = [
		("Rating", "Рейтинг"),
		("ADR", "ADR"),
		("KAST", "KAST"),
		("K", "K"),
		("D", "D"),
		("OpK-D", "OpK-D"),
		("MKs", "MKs"),
		("1vsX", "1vsX"),
		("HS", "HS"),
		("A", "A"),
		("A_f", "A_f"),
		("D_t", "D_t")
	]
	# Добавляем кнопки по 2 в ряд
	buttons = [InlineKeyboardButton(text=label, callback_data=f"graph_{name}_{metric}") for metric, label in metrics]
	for i in range(0, len(buttons), 2):
		keyboard.row(*buttons[i:i+2])
	await call.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')


async def playerstat_callback(call: types.CallbackQuery, as_new_message=False):
	"""Обработчик для показа статистики игрока"""
	name = call.data[len('playerstat_'):]
	stats = get_player_stats(name)
	text, keyboard = render_player_card(name, stats, with_keyboard=True)
	log_history(call.from_user.id, call.from_user.username, 'view_player_card', {'player': name})
	if as_new_message:
		await call.message.answer(text, reply_markup=keyboard, parse_mode='HTML')
	else:
		await call.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')


async def back_players_callback(call: types.CallbackQuery):
	"""Обработчик для возврата к списку игроков"""
	from handlers import cmd_players
	await cmd_players(call.message)


async def show_map_callback(call: types.CallbackQuery, as_new_message=False):
	"""Обработчик для показа статистики карты"""
	map_name = call.data[len('show_map_'):]
	stats = get_map_stats(map_name)
	description = (
		f'🗺️ <b>Карта: {map_name.capitalize()}</b>\n\n'
		f'📊 <b>Статистика BakS eSports на {map_name}:</b>\n'
		f'В таблице показаны все официальные матчи команды на этой карте.\n\n'
		f'📋 <b>Информация в таблице:</b>\n'
		f'• <b>Дата</b> — когда проходил матч\n'
		f'• <b>Соперник</b> — команда противника\n'
		f'• <b>Счёт</b> — итоговый результат карты\n'
		f'• <b>WinRate</b> — процент побед (в разработке)\n\n'
		f'🔄 <b>Навигация:</b> Используйте кнопку ниже для возврата к списку карт.'
	)
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
		keyboard.add(InlineKeyboardButton(text="⬅️ Назад к списку карт", callback_data="back_maps"))
		keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_map_{map_name}"))
		user = call.from_user or (call.message and call.message.from_user)
		if user:
			log_history(user.id, user.username, 'view_map', {'map': map_name})
		if as_new_message:
			await call.message.answer(f'{description}\n<pre>{table}</pre>', reply_markup=keyboard, parse_mode='HTML')
		else:
			await call.message.edit_text(f'{description}\n<pre>{table}</pre>', reply_markup=keyboard, parse_mode='HTML')
	else:
		if as_new_message:
			await call.message.answer('❌ Карта не найдена. Попробуйте выбрать другую из списка.')
		else:
			await call.message.edit_text('❌ Карта не найдена. Попробуйте выбрать другую из списка.')


async def back_maps_callback(call: types.CallbackQuery):
	"""Обработчик для возврата к списку карт"""
	from handlers import cmd_maps
	await cmd_maps(call.message)


async def match_info_callback(call: types.CallbackQuery, as_new_message=False):
	"""Обработчик для показа информации о матче"""
	idx = int(call.data.split('_')[1])
	match = get_match_by_index(idx)
	if not match:
		if as_new_message:
			await call.message.answer('❌ Матч не найден.')
		else:
			await call.message.edit_text('❌ Матч не найден.')
		return
	opp = [team for team in match['teams'] if team != 'BAKS'][0]
	text = (
		f"🏆 <b>Детальный анализ матча</b>\n\n"
		f"⚔️ <b>BakS eSports</b> vs <b>{opp}</b>\n"
		f"📅 <b>Дата:</b> {match['date']}\n"
		f"🏆 <b>Итоговый счёт:</b> <code>{match['score']}</code>\n\n"
		f"🗺️ <b>Карты матча:</b>\n"
	)
	from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
	keyboard = InlineKeyboardMarkup()
	for i, m in enumerate(match['maps'], 1):
		text += f"   • <b>{m['name']}</b> — <code>{m['score']}</code>\n"
		keyboard.add(
			InlineKeyboardButton(
				text=f"{m['name']}", callback_data=f"matchmap_{idx}_{i}"
			)
		)
	keyboard.add(InlineKeyboardButton(text="⬅️ Назад к турнирам", callback_data="back_tournaments"))
	keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_match_{idx}"))
	team = match['overall']['team_stats']
	text += f"\n📊 <b>Командная статистика:</b>\n"
	text += f"• ⭐ Рейтинг команды: <code>{team['team_rating']}</code>\n"
	text += f"• 🎯 Первые убийства: <code>{team['first_kills']}</code>\n"
	text += f"• 💪 Клатчи: <code>{team['clutches_won']}</code>\n"
	players = sorted(match['overall']['players']['both'], key=lambda p: p['Rating'], reverse=True)[:3]
	text += "\n🏅 <b>Топ-игроки матча:</b>\n"
	for i, p in enumerate(players, 1):
		text += f"{i}. <b>{p['nickname']}</b> — рейтинг <code>{p['Rating']}</code> (<code>{p['K']}K</code>)\n"
	from tabulate import tabulate
	table = tabulate(
		[{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in match['overall']['players']['both']],
		headers="keys", tablefmt="fancy_grid"
	)
	text += f"\n📊 <b>Полная статистика игроков:</b>\n<pre>{table}</pre>"
	user = call.from_user or (call.message and call.message.from_user)
	if user:
		log_history(user.id, user.username, 'view_match', {'match_idx': idx})
	if as_new_message:
		await call.message.answer(text, reply_markup=keyboard, parse_mode='HTML')
	else:
		await call.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')


async def back_to_tournaments(call: types.CallbackQuery):
	"""Обработчик для возврата к турнирам"""
	from handlers import cmd_tournaments
	await cmd_tournaments(call.message)


async def match_map_callback(call: types.CallbackQuery, as_new_message=False):
	"""Обработчик для показа карты матча"""
	_, match_idx, map_idx = call.data.split('_', maxsplit=2)
	match_idx, map_idx = int(match_idx), int(map_idx)
	match = get_match_by_index(match_idx)
	if not match:
		if as_new_message:
			await call.message.answer('❌ Матч не найден.')
		else:
			await call.message.edit_text('❌ Матч не найден.')
		return
	m = match['maps'][map_idx - 1]
	text = (
		f"🗺️ <b>Анализ карты</b>\n\n"
		f"📋 <b>Карта:</b> <b>{m['name']}</b>\n"
		f"🏆 <b>Счёт:</b> <code>{m['score']}</code>\n"
		f"📊 <b>Раунды по половинам:</b> <code>{' / '.join(m['breakdown']['halves'])}</code>\n\n"
	)
	best = max(m['players']['both'], key=lambda p: p['Rating'])
	text += f"🏅 <b>MVP карты:</b> <b>{best['nickname']}</b>\n"
	text += f"⭐ Рейтинг: <code>{best['Rating']}</code> | 💥 ADR: <code>{best['ADR']}</code> | ⚔️ K/D: <code>{best['K']}K/{best['D']}D</code>\n\n"
	# Таблица всех игроков (карта)
	table = tabulate(
		[{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in m['players']['both']],
		headers="keys", tablefmt="fancy_grid"
	)
	text += f"📊 <b>Статистика игроков на {m['name']}:</b>\n<pre>{table}</pre>"
	from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
	keyboard = InlineKeyboardMarkup()
	keyboard.add(
		InlineKeyboardButton(text="🎯 T-сторона", callback_data=f"matchmap_side_{match_idx}_{map_idx}_t"),
		InlineKeyboardButton(text="🛡️ CT-сторона", callback_data=f"matchmap_side_{match_idx}_{map_idx}_ct")
	)
	# Кнопка назад к матчу
	keyboard.add(InlineKeyboardButton(text="⬅️ Назад к матчу", callback_data=f"match_{match_idx}"))
	# Кнопка экспорта: экспортировать таблицу игроков на карте
	keyboard.add(InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_matchmap_{match_idx}_{map_idx}"))
	if as_new_message:
		await call.message.answer(text, reply_markup=keyboard)
	else:
		await call.message.edit_text(text, reply_markup=keyboard)


async def match_map_side_callback(call: types.CallbackQuery, as_new_message=False):
	"""Обработчик для показа стороны карты"""
	_, _, match_idx, map_idx, side = call.data.split('_', maxsplit=4)
	match_idx, map_idx = int(match_idx), int(map_idx)
	match = get_match_by_index(match_idx)
	if not match or map_idx > len(match['maps']):
		if as_new_message:
			await call.message.answer('Нет данных для экспорта.')
		else:
			await call.message.edit_text('Нет данных для экспорта.')
		return
	m = match['maps'][map_idx - 1]
	players = m['players'][side]
	# Таблица игроков по сторонам (T/CT)
	table = tabulate(
		[{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in players],
		headers="keys", tablefmt="fancy_grid"
	)
	side_name = "Terrorist" if side == "t" else "Counter-Terrorist"
	text = f"🎯 <b>{side_name}-сторона</b> на карте <b>{m['name']}</b>\n\n📊 <b>Статистика игроков:</b>\n<pre>{table}</pre>"
	from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
	keyboard = InlineKeyboardMarkup()
	# Кнопка назад к карте
	keyboard.add(InlineKeyboardButton(text="⬅️ Назад к карте", callback_data=f"matchmap_{match_idx}_{map_idx}"))
	# Кнопка экспорта: экспортировать таблицу игроков по стороне
	keyboard.add(
		InlineKeyboardButton(text="📤 Экспорт", callback_data=f"export_table_matchmap_side_{match_idx}_{map_idx}_{side}")
	)
	if as_new_message:
		await call.message.answer(text, reply_markup=keyboard)
	else:
		await call.message.edit_text(text, reply_markup=keyboard)


async def players_chart_menu(call: types.CallbackQuery):
	"""Обработчик для меню диаграммы игроков"""
	keyboard = players_chart_keyboard()
	await call.message.edit_reply_markup(reply_markup=keyboard)
	await call.answer('Выберите метрику для диаграммы:')


async def players_chart_build(call: types.CallbackQuery):
	"""Обработчик для построения диаграммы игроков"""
	metric = call.data[len('players_chart_'):]
	players_avg = get_player_averages()
	sorted_players = sorted(players_avg.items(), key=lambda x: x[1]['Rating'], reverse=True)
	names = [nickname for nickname, _ in sorted_players]
	if metric == 'rating':
		values = [stats['Rating'] for _, stats in sorted_players]
		label = 'Рейтинг'
	elif metric == 'adr':
		values = [stats['ADR'] for _, stats in sorted_players]
		label = 'ADR'
	elif metric == 'kast':
		values = [stats['KAST'] for _, stats in sorted_players]
		label = 'KAST (%)'
	elif metric == 'kd':
		values = [stats['K'] / stats['D'] if stats['D'] else 0 for _, stats in sorted_players]
		label = 'K/D'
	elif metric == 'hs':
		values = [stats['HS'] for _, stats in sorted_players]
		label = 'HS%'
	elif metric == 'opkd':
		values = [stats['OpK-D'] for _, stats in sorted_players]
		label = 'OpK-D'
	else:
		await call.answer('Неизвестная метрика.')
		return
	plt.figure(figsize=(8, 4))
	plt.bar(names, values, color='#4e79a7')
	plt.title(f'{label} всех игроков BakS eSports')
	plt.xlabel('Игрок')
	plt.ylabel(label)
	plt.xticks(rotation=30)
	plt.tight_layout()
	buf = io.BytesIO()
	plt.savefig(buf, format='png')
	buf.seek(0)
	plt.close()
	await call.message.answer_photo(buf, caption=f'📊 {label} всех игроков BakS eSports')
	await call.answer()


async def players_chart_cancel(call: types.CallbackQuery):
	"""Обработчик для отмены диаграммы игроков"""
	from handlers import cmd_players
	await cmd_players(call.message)


async def progress_chart_callback(call: types.CallbackQuery):
	"""Обработчик для диаграммы прогресса"""
	players = get_players()
	progress = []
	for player in players:
		stats = get_player_stats(player)
		if len(stats) >= 2:
			first = stats[0]['Rating']
			last = stats[-1]['Rating']
			progress.append((player, first, last))
	if not progress:
		await call.answer('Нет данных для построения графика.')
		return
	names = [p for p, _, _ in progress]
	changes = [l - f for _, f, l in progress]
	plt.figure(figsize=(8, 4))
	bars = plt.bar(names, changes, color=['#4e79a7' if c >= 0 else '#e15759' for c in changes])
	plt.title('Изменение рейтинга игроков BakS eSports')
	plt.xlabel('Игрок')
	plt.ylabel('Δ Рейтинг (последний - первый)')
	plt.axhline(0, color='gray', linewidth=0.8)
	plt.xticks(rotation=30)
	plt.tight_layout()
	buf = io.BytesIO()
	plt.savefig(buf, format='png')
	buf.seek(0)
	plt.close()
	await call.message.answer_photo(buf, caption='📊 Изменение рейтинга игроков (Δ = последний - первый матч)')
	await call.answer()


async def graph_callback(call: types.CallbackQuery):
	"""Обработчик для графиков игроков"""
	_, name, metric = call.data.split('_', maxsplit=2)
	stats = get_player_stats(name)
	if not stats:
		await call.message.edit_text('Игрок не найден.')
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
	await call.message.answer_photo(buf, caption=f'{name} — {metric} по матчам')
	plt.close()


async def export_table_choose_format(call: types.CallbackQuery):
	"""Обработчик для выбора формата экспорта"""
	cb = call.data[len('export_table_'):]
	keyboard = export_format_keyboard(cb)
	desc = 'Выберите формат для экспорта:'
	await call.message.edit_reply_markup(reply_markup=keyboard)
	await call.answer(desc)


async def export_table_send(call: types.CallbackQuery):
	"""Универсальный обработчик экспорта файлов"""
	# --- Импортируем необходимые функции ---
	from data_loader import get_player_stats, get_players, get_maps, get_map_stats
	from export_utils import export_data, log_history
	from aiogram.types import InputFile

	# export_tablefmt_<type>_<id...>_<fmt>
	parts = call.data[len('export_tablefmt_'):].rsplit('_', 1)
	if len(parts) != 2:
		await call.message.answer('Ошибка формата callback.')
		return
	cb_data, fmt = parts[0], parts[1]
	cb_parts = cb_data.split('_')

	# --- Экспорт средней статистики всех игроков (таблица) ---
	if cb_parts[0] == 'players':
		from data_loader import get_player_averages
		players_avg = get_player_averages()
		if not players_avg:
			await call.message.answer('Нет данных для экспорта.')
			return
		data = [{
			"Игрок": nickname,
			"Средний рейтинг": f"{stats['Rating']:.2f}",
			"Средний ADR": f"{stats['ADR']:.1f}",
			"Средний KAST": f"{stats['KAST']:.1f}%",
			"Средний K/D": f"{stats['K'] / stats['D'] if stats['D'] else 0:.2f}",
			"Средний HS%": f"{stats['HS']:.1f}%"
		} for nickname, stats in players_avg.items()]
		desc = 'Средняя статистика всех игроков'
		filename = 'players_average_stats'

	# --- Экспорт списка всех карт ---
	elif cb_parts[0] == 'maps':
		maps = get_maps()
		data = [{"Карта": map_name, "Количество матчей": len(get_map_stats(map_name))} for map_name in maps]
		desc = 'Список всех карт с количеством матчей'
		filename = 'maps_list'

	# --- Экспорт статистики игрока за матч ---
	elif cb_parts[0] == 'player' and cb_parts[1] == 'match':
		# export_table_player_match_{name}_{idx}
		player_name = cb_parts[2]
		match_idx = int(cb_parts[3])
		stats = get_player_stats(player_name)
		if not stats or match_idx < 0 or match_idx >= len(stats):
			await call.message.answer('Нет данных для экспорта.')
			return
		s = stats[match_idx]
		data = [{
			"Дата": s.get("date", "-"),
			"Турнир": s.get("tournament", "-"),
			"Соперник": s.get("opponent", "-"),
			"K": s.get("K", "-"),
			"D": s.get("D", "-"),
			"ADR": s.get("ADR", "-"),
			"KAST": s.get("KAST", "-"),
			"OpK-D": s.get("OpK-D", "-"),
			"MKs": s.get("MKs", "-"),
			"1vsX": s.get("1vsX", "-"),
			"HS": s.get("HS", "-"),
			"A": s.get("A", "-"),
			"A_f": s.get("A_f", "-"),
			"D_t": s.get("D_t", "-"),
			"Rating": s.get("Rating", "-")
		}]
		desc = f'Статистика игрока {player_name} за матч {s.get("date", "-")} vs {s.get("opponent", "-")}'
		filename = f'player_{player_name}_match_{match_idx}_stats'

	# --- Экспорт матча ---
	elif cb_parts[0] == 'match':
		from data_loader import get_match_by_index
		match_idx = int(cb_parts[1])
		match = get_match_by_index(match_idx)
		if not match:
			await call.message.answer('Матч не найден.')
			return
		opp = [team for team in match['teams'] if team != 'BAKS'][0]
		data = [{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in match['overall']['players']['both']]
		desc = f'Статистика матча BakS vs {opp} ({match["date"]})'
		filename = f'match_{match_idx}_stats'

	# --- Экспорт стороны карты ---
	elif cb_parts[0] == 'matchmap' and cb_parts[1] == 'side':
		from data_loader import get_match_by_index
		match_idx, map_idx, side = int(cb_parts[2]), int(cb_parts[3]), cb_parts[4]
		match = get_match_by_index(match_idx)
		if not match or map_idx > len(match['maps']):
			await call.message.answer('Данные не найдены.')
			return
		m = match['maps'][map_idx - 1]
		players = m['players'][side]
		data = [{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in players]
		side_name = "T" if side == "t" else "CT"
		desc = f'Статистика {side_name}-стороны на {m["name"]} (матч {match_idx})'
		filename = f'match_{match_idx}_map_{m["name"]}_{side_name}_stats'

	# --- Экспорт карты матча ---
	elif cb_parts[0] == 'matchmap':
		from data_loader import get_match_by_index
		match_idx, map_idx = int(cb_parts[1]), int(cb_parts[2])
		match = get_match_by_index(match_idx)
		if not match or map_idx > len(match['maps']):
			await call.message.answer('Данные не найдены.')
			return
		m = match['maps'][map_idx - 1]
		data = [{
			"Игрок": p["nickname"],
			"K/D": f'{p["K"]}/{p["D"]}',
			"ADR": p["ADR"],
			"KAST": p["KAST"],
			"OpK-D": p["OpK-D"],
			"MKs": p["MKs"],
			"1vsX": p.get("1vsX", 0),
			"HS": p["HS"],
			"A": p["A"],
			"A_f": p["A_f"],
			"D_t": p["D_t"],
			"Rating": p["Rating"]
		} for p in m['players']['both']]
		desc = f'Статистика на карте {m["name"]} (матч {match_idx})'
		filename = f'match_{match_idx}_map_{m["name"]}_stats'

	# --- Экспорт статистики игрока по всем матчам ---
	elif cb_parts[0] == 'player':
		player_name = cb_parts[1]
		stats = get_player_stats(player_name)
		if not stats:
			await call.message.answer('Нет данных для экспорта.')
			return
		data = [{
			"Дата": s.get("date", "-"),
			"Турнир": s.get("tournament", "-"),
			"Соперник": s.get("opponent", "-"),
			"K": s.get("K", "-"),
			"D": s.get("D", "-"),
			"ADR": s.get("ADR", "-"),
			"KAST": s.get("KAST", "-"),
			"OpK-D": s.get("OpK-D", "-"),
			"MKs": s.get("MKs", "-"),
			"1vsX": s.get("1vsX", "-"),
			"HS": s.get("HS", "-"),
			"A": s.get("A", "-"),
			"A_f": s.get("A_f", "-"),
			"D_t": s.get("D_t", "-"),
			"Rating": s.get("Rating", "-")
		} for s in stats]
		desc = f'Статистика игрока {player_name} по всем матчам'
		filename = f'player_{player_name}_all_matches_stats'

	# --- Экспорт статистики по карте ---
	elif cb_parts[0] == 'map':
		map_name = cb_parts[1]
		stats = get_map_stats(map_name)
		if not stats:
			await call.message.answer('Нет данных для экспорта.')
			return
		data = [{
			"Дата": m.get("date", "-"),
			"Соперник": m.get("opponent", "-"),
			"Счёт": m.get("score", "-"),
			"WinRate": "-"
		} for m in stats]
		desc = f'Статистика по карте {map_name}'
		filename = f'map_{map_name}_stats'

	# --- Экспорт турниров с количеством матчей ---
	elif cb_parts[0] == 'tournaments':
		from data_loader import get_tournaments
		tournaments = get_tournaments()
		data = [{"Турнир": t, "Количество матчей": len(matches)} for t, matches in tournaments.items()]
		desc = 'Список всех турниров'
		filename = 'tournaments_list'

	else:
		await call.message.answer('Экспорт для этого типа данных не реализован.')
		return

	# Экспортируем данные
	try:
		file_data = export_data(data, desc, filename, fmt)
		await call.message.answer_document(
			InputFile(file_data, filename=f"{filename}.{fmt}"),
			caption=f"📤 {desc}"
		)
		await call.answer('✅ Файл экспортирован!')
		
		# Сохраняем в историю
		user = call.from_user or (call.message and call.message.from_user)
		if user:
			log_history(user.id, user.username, 'export', {
				'type': cb_parts[0],
				'filename': filename,
				'format': fmt
			})
			
	except Exception as e:
		await call.message.answer(f'❌ Ошибка при экспорте: {str(e)}')
		await call.answer('❌ Ошибка экспорта')


async def export_cancel_callback(call: types.CallbackQuery):
	"""Обработчик для отмены экспорта - возвращает к предыдущему меню по типу данных"""
	await call.message.delete()  # Удаляем сообщение с экспортом

	cb = call.data[len('export_cancel_'):] if call.data.startswith('export_cancel_') else ''

	if cb.startswith('players'):
		from handlers import cmd_players
		await cmd_players(call.message)
	elif cb.startswith('maps'):
		from handlers import cmd_maps
		await cmd_maps(call.message)
	elif cb.startswith('map_'):
		map_name = cb[4:]
		from callbacks import show_map_callback
		class DummyCall:
			def __init__(self, message, from_user, data):
				self.message = message
				self.from_user = from_user
				self.data = f'show_map_{map_name}'
		await show_map_callback(DummyCall(call.message, call.from_user, f'show_map_{map_name}'), as_new_message=True)
	elif cb.startswith('matchmap_side_'):
		# export_cancel_matchmap_side_{match_idx}_{map_idx}_{side}
		parts = cb.split('_')
		if len(parts) >= 5:
			match_idx = int(parts[2])
			map_idx = int(parts[3])
			side = parts[4]
			from callbacks import match_map_side_callback
			class DummyCall:
				def __init__(self, message, from_user, data):
					self.message = message
					self.from_user = from_user
					self.data = f'matchmap_side_{match_idx}_{map_idx}_{side}'
			await match_map_side_callback(DummyCall(call.message, call.from_user, f'matchmap_side_{match_idx}_{map_idx}_{side}'), as_new_message=True)
		else:
			from handlers import cmd_tournaments
			await cmd_tournaments(call.message)
	elif cb.startswith('matchmap_'):
		# export_cancel_matchmap_{match_idx}_{map_idx}
		parts = cb.split('_')
		if len(parts) >= 3:
			match_idx = int(parts[1])
			map_idx = int(parts[2])
			from callbacks import match_map_callback
			class DummyCall:
				def __init__(self, message, from_user, data):
					self.message = message
					self.from_user = from_user
					self.data = f'matchmap_{match_idx}_{map_idx}'
			await match_map_callback(DummyCall(call.message, call.from_user, f'matchmap_{match_idx}_{map_idx}'), as_new_message=True)
		else:
			from handlers import cmd_tournaments
			await cmd_tournaments(call.message)
	elif cb.startswith('tournaments'):
		from handlers import cmd_tournaments
		await cmd_tournaments(call.message)
	elif cb.startswith('match_'):
		match_idx = int(cb[len('match_'):])
		from callbacks import match_info_callback
		class DummyCall:
			def __init__(self, message, from_user, data):
				self.message = message
				self.from_user = from_user
				self.data = f'match_{match_idx}'
		await match_info_callback(DummyCall(call.message, call.from_user, f'match_{match_idx}'), as_new_message=True)
	elif cb.startswith('player_match_'):
		# export_cancel_player_match_{name}_{idx}
		parts = cb.split('_')
		if len(parts) >= 3:
			name = parts[2]
			from callbacks import playerstat_callback
			class DummyCall:
				def __init__(self, message, from_user, data):
					self.message = message
					self.from_user = from_user
					self.data = f'playerstat_{name}'
			await playerstat_callback(DummyCall(call.message, call.from_user, f'playerstat_{name}'), as_new_message=True)
		else:
			from handlers import cmd_players
			await cmd_players(call.message)
	elif cb.startswith('playerstat_') or cb.startswith('player_'):
		from callbacks import playerstat_callback
		name = cb[len('playerstat_'):] if cb.startswith('playerstat_') else cb[len('player_'):]
		class DummyCall:
			def __init__(self, message, from_user, data):
				self.message = message
				self.from_user = from_user
				self.data = f'playerstat_{name}'
		await playerstat_callback(DummyCall(call.message, call.from_user, f'playerstat_{name}'), as_new_message=True)
	else:
		from handlers import cmd_start
		await cmd_start(call.message)
