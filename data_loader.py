import json
import os
from config import DATA_PATH

# Загрузка данных из baks_stats.json
with open(DATA_PATH, encoding='utf-8') as f:
    STATS = json.load(f)


def get_tournaments():
    """Возвращает словарь турниров с матчами"""
    tournaments = {}
    for match in STATS['match_info']:
        t = match['tournament']
        if t not in tournaments:
            tournaments[t] = []
        tournaments[t].append(match)
    return tournaments


def get_games(tournament=None):
    """Возвращает список игр с возможностью фильтрации по турниру"""
    games = []
    for match in STATS['match_info']:
        if tournament is None or match['tournament'] == tournament:
            for i, m in enumerate(match['maps'], 1):
                games.append({
                    'id': f"{match['date']}#{i}",
                    'tournament': match['tournament'],
                    'opponent': [t for t in match['teams'] if t != 'BAKS'][0],
                    'score': m['score'],
                    'map': m['name'],
                    'date': match['date'],
                    'mvp': max(m['players']['both'], key=lambda p: p.get('Rating', 0))['nickname'] if m['players']['both'] else '-'
                })
    return games


def get_players():
    """Возвращает список всех игроков"""
    players = {}
    for match in STATS['match_info']:
        for p in match['overall']['players']['both']:
            players[p['nickname']] = p
    return list(players.keys())


def get_player_stats(nickname):
    """Возвращает статистику игрока по всем матчам"""
    stats = []
    for match in STATS['match_info']:
        opponent = [t for t in match['teams'] if t != 'BAKS'][0]
        for p in match['overall']['players']['both']:
            if p['nickname'].lower() == nickname.lower():
                stats.append({
                    'tournament': match['tournament'],
                    'date': match['date'],
                    'opponent': opponent,
                    'K': p['K'],
                    'D': p['D'],
                    'ADR': p['ADR'],
                    'Rating': p['Rating'],
                    'KAST': p['KAST'],
                    'OpK-D': p['OpK-D'],
                    'MKs': p['MKs'],
                    '1vsX': p.get('1vsX', 0),
                    'HS': p['HS'],
                    'A': p['A'],
                    'A_f': p['A_f'],
                    'D_t': p['D_t']
                })
    return stats


def get_maps():
    """Возвращает словарь карт с матчами"""
    maps = {}
    for match in STATS['match_info']:
        for m in match['maps']:
            map_copy = m.copy()
            map_copy['date'] = match['date']
            map_copy['tournament'] = match['tournament']
            map_copy['opponent'] = [t for t in match['teams'] if t != 'BAKS'][0]
            if m['name'] not in maps:
                maps[m['name']] = []
            maps[m['name']].append(map_copy)
    return maps


def get_map_stats(map_name):
    """Возвращает статистику по конкретной карте"""
    maps = get_maps()
    return maps.get(map_name.capitalize(), [])


def get_match_by_index(idx):
    """Возвращает матч по индексу (1-based)"""
    matches = []
    for t_matches in get_tournaments().values():
        matches.extend(t_matches)
    if 1 <= idx <= len(matches):
        return matches[idx - 1]
    return None


def get_match_list():
    """Возвращает список всех матчей"""
    matches = []
    for t_matches in get_tournaments().values():
        matches.extend(t_matches)
    return matches


def get_best_map_for_player(nickname):
    """Возвращает лучшую карту игрока"""
    best = None
    best_rating = 0
    for match in STATS['match_info']:
        for m in match['maps']:
            for p in m['players']['both']:
                if p['nickname'].lower() == nickname.lower() and p['Rating'] > best_rating:
                    best_rating = p['Rating']
                    best = (m['name'], best_rating)
    return best


def get_last_match_for_player(nickname):
    """Возвращает последний матч игрока"""
    for match in reversed(STATS['match_info']):
        for p in match['overall']['players']['both']:
            if p['nickname'].lower() == nickname.lower():
                return match
    return None


def get_side_stats(map_stats, side):
    """Возвращает статистику по стороне карты"""
    return map_stats['players'][side]


def get_player_averages():
    """Возвращает средние показатели всех игроков по всем матчам"""
    players_avg = {}
    players_count = {}

    def safe_float(value):
        """Безопасно конвертирует значение в float"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            clean_value = value.replace('%', '').replace(' ', '')
            try:
                return float(clean_value)
            except:
                return 0.0
        else:
            return 0.0

    for match in STATS['match_info']:
        for p in match['overall']['players']['both']:
            nickname = p['nickname']
            if nickname not in players_avg:
                players_avg[nickname] = {
                    'K': 0, 'D': 0, 'ADR': 0, 'Rating': 0, 'KAST': 0,
                    'OpK-D': 0, 'MKs': 0, '1vsX': 0, 'HS': 0, 'A': 0, 'A_f': 0, 'D_t': 0
                }
                players_count[nickname] = 0

            players_count[nickname] += 1
            players_avg[nickname]['K'] += safe_float(p['K'])
            players_avg[nickname]['D'] += safe_float(p['D'])
            players_avg[nickname]['ADR'] += safe_float(p['ADR'])
            players_avg[nickname]['Rating'] += safe_float(p['Rating'])
            players_avg[nickname]['OpK-D'] += safe_float(p['OpK-D'])
            players_avg[nickname]['MKs'] += safe_float(p['MKs'])
            players_avg[nickname]['1vsX'] += safe_float(p.get('1vsX', 0))
            players_avg[nickname]['HS'] += safe_float(p['HS'])
            players_avg[nickname]['A'] += safe_float(p['A'])
            players_avg[nickname]['A_f'] += safe_float(p['A_f'])
            players_avg[nickname]['D_t'] += safe_float(p['D_t'])
            players_avg[nickname]['KAST'] += safe_float(p['KAST'])

    for nickname in players_avg:
        count = players_count[nickname]
        for key in players_avg[nickname]:
            players_avg[nickname][key] = round(players_avg[nickname][key] / count, 2)

    return players_avg 