import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_polling
from config import API_TOKEN, LOG_LEVEL
from handlers import (
	cmd_start, cmd_help, cmd_abbr, cmd_players, cmd_maps, cmd_tournaments, cmd_progress, cmd_player, cmd_map, cmd_graph,
	cmd_alert, unknown, cmd_history
)
from callbacks import (
	player_match_callback, playerstat_callback, back_players_callback, show_map_callback, back_maps_callback,
	match_info_callback, back_to_tournaments, match_map_callback, match_map_side_callback,
	players_chart_menu, players_chart_build, players_chart_cancel, progress_chart_callback, graph_callback,
	export_table_choose_format, export_cancel_callback, export_table_send
)
from keyboards import main_menu

logging.basicConfig(level=LOG_LEVEL)
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

# --- Регистрация хендлеров ---
dp.register_message_handler(cmd_start, commands=['start'])
dp.register_message_handler(cmd_help, commands=['help'])
dp.register_message_handler(cmd_abbr, commands=['abbr'])
dp.register_message_handler(cmd_players, commands=['players'])
dp.register_message_handler(cmd_maps, commands=['maps'])
dp.register_message_handler(cmd_tournaments, commands=['tournaments'])
dp.register_message_handler(cmd_progress, commands=['progress'])
dp.register_message_handler(cmd_player, commands=['player'])
dp.register_message_handler(cmd_map, lambda m: m.text and m.text.startswith('/map'))
dp.register_message_handler(cmd_graph, commands=['graph'])
dp.register_message_handler(cmd_alert, commands=['alert'])
dp.register_message_handler(cmd_history, commands=['history'])

# --- Обработка текстовых кнопок меню ---
dp.register_message_handler(cmd_players, lambda m: m.text == '👥 Игроки')
dp.register_message_handler(cmd_maps, lambda m: m.text == '🗺️ Карты')
dp.register_message_handler(cmd_tournaments, lambda m: m.text == '🏆 Турниры')
dp.register_message_handler(cmd_progress, lambda m: m.text == '📈 Прогресс')
dp.register_message_handler(cmd_abbr, lambda m: m.text == 'ℹ️ Аббревиатуры')
dp.register_message_handler(cmd_help, lambda m: m.text == '❓ Помощь')
dp.register_message_handler(cmd_start, lambda m: m.text == '🔄 Перезапуск (/start)')
dp.register_message_handler(cmd_history, lambda m: m.text == '🕓 История')

dp.register_message_handler(unknown)

# --- Callback-хендлеры ---
dp.register_callback_query_handler(player_match_callback, lambda c: c.data.startswith('player_match_'))
dp.register_callback_query_handler(playerstat_callback, lambda c: c.data.startswith('playerstat_'))
dp.register_callback_query_handler(back_players_callback, lambda c: c.data == 'back_players')
dp.register_callback_query_handler(show_map_callback, lambda c: c.data.startswith('show_map_'))
dp.register_callback_query_handler(back_maps_callback, lambda c: c.data == 'back_maps')
dp.register_callback_query_handler(
	match_info_callback, lambda c: c.data.startswith('match_') and not c.data.startswith('matchmap_')
)
dp.register_callback_query_handler(back_to_tournaments, lambda c: c.data == 'back_tournaments')
dp.register_callback_query_handler(
	match_map_callback, lambda c: c.data.startswith('matchmap_') and not c.data.startswith('matchmap_side_')
)
dp.register_callback_query_handler(match_map_side_callback, lambda c: c.data.startswith('matchmap_side_'))
dp.register_callback_query_handler(players_chart_menu, lambda c: c.data == 'players_chart')
dp.register_callback_query_handler(
	players_chart_build, lambda c: c.data.startswith('players_chart_') and c.data != 'players_chart_cancel'
)
dp.register_callback_query_handler(players_chart_cancel, lambda c: c.data == 'players_chart_cancel')
dp.register_callback_query_handler(progress_chart_callback, lambda c: c.data == 'progress_chart')
dp.register_callback_query_handler(graph_callback, lambda c: c.data.startswith('graph_'))
dp.register_callback_query_handler(export_table_choose_format, lambda c: c.data.startswith('export_table_'))
dp.register_callback_query_handler(export_cancel_callback, lambda c: c.data and c.data.startswith('export_cancel'))
dp.register_callback_query_handler(export_table_send, lambda c: c.data.startswith('export_tablefmt_'))

if __name__ == '__main__':
	start_polling(dp, skip_updates=True)
