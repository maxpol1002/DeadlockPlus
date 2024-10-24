import math
import pytz
import requests

from datetime import datetime

from steamfunc import get_user_playtime, get_users_data, usteamid_to_commid


def get_hero_stats(hero_name: str):
    url = f"https://assets.deadlock-api.com/v1/heroes/by-name/{hero_name}?language=english"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data

    else:
        print(response.status_code)


def get_all_heroes():
    url = "https://assets.deadlock-api.com/v1/heroes?language=english"
    all_heroes = requests.get(url).json()
    return all_heroes


def get_hero_by_id(all_heroes, hero_id: int) -> str or None:
    for hero in all_heroes:
        if hero['id'] == hero_id:
            return hero['name']

    return None


def get_hero_icon(hero_name: str) -> str:
    hero_icons = {
        "Abrams": "😈",
        "Bebop": "🤖",
        "Dynamo": "❎",
        "Grey Talon": "🏹",
        "Haze": "😶‍🌫️",
        "Infernus": "🔥",
        "Ivy": "🗿",
        "Kelvin": "🥶",
        "Lady Geist": "🔫",
        "Lash": "👨‍🦰",
        "McGinnis": "🚀",
        "Mirage": "🌪",
        "Mo & Krill": "🐽",
        "Paradox": "🔄",
        "Pocket": "💼",
        "Seven": "⚡️",
        "Shiv": "🩸",
        "Vindicta": "🎯",
        "Viscous": "🟢",
        "Warden": "👮‍♂️",
        "Wraith": "🃏",
        "Yamato": "⛩"
    }

    return hero_icons.get(hero_name, "")


def get_user_hero(match_data, user_uid) -> str:
    for player in match_data['players']:
        if player['account_id'] == user_uid:
            return player['hero']


def get_active_matches() -> list:
    url = "https://data.deadlock-api.com/active-matches"
    response = requests.get(url)
    if response.status_code == 200:
        active_matches = response.json()
        return active_matches

    return []


def get_hero_winrates(min_elo, max_elo, min_ts, max_ts):
    url = f"https://analytics.deadlock-api.com/v1/hero-win-loss-stats?" \
          f"min_match_score={min_elo}&max_match_score={max_elo}&min_unix_timestamp={min_ts}&max_unix_timestamp={max_ts}"
    response = requests.get(url)
    if response.status_code == 200:
        hero_winrates = response.json()
        return hero_winrates

    return []


def sort_matches_byelo(matches, reverse: bool):
    if reverse:
        sorted_matches = sorted(matches, key=lambda x: x['match_score'], reverse=True)
    else:
        sorted_matches = sorted(matches, key=lambda x: x['match_score'])

    return sorted_matches


def get_top_matches(active_matches, count: int):
    sorted_matches = sort_matches_byelo(active_matches, reverse=True)
    top_matches = sorted_matches[:count]
    return top_matches


def get_current_minmaxelo() -> tuple[int, int]:
    active_matches = get_active_matches()
    sorted_matches = sort_matches_byelo(active_matches, reverse=True)
    max_elo = sorted_matches[0].get("match_score")
    min_elo = sorted_matches[-1].get("match_score")
    return max_elo, min_elo


def parse_match_time(timestamp) -> datetime:
    tz = pytz.timezone('Europe/Kyiv')
    utc_time = datetime.utcfromtimestamp(timestamp)
    kyiv_time = pytz.utc.localize(utc_time).astimezone(tz)

    return kyiv_time


def find_match_byid(match_id, active_matches) -> dict or None:
    for match in active_matches:
        if match.get("match_id") == match_id:
            return match

    return None


def parse_match_duration(start_time) -> str:
    duration_seconds = (datetime.now(pytz.timezone('Europe/Kyiv')) - start_time).total_seconds()
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    duration = f"{minutes}:{seconds:02d}"

    return duration


def filter_match_data(match_id, active_matches) -> dict or str:
    data = find_match_byid(match_id, active_matches)
    if data:
        heroes = get_all_heroes()
        players_accids = [player["account_id"] for player in data["players"]]
        players_data = get_users_data(players_accids)
        start_time = parse_match_time(data["start_time"])
        page_number, match_number = find_match_position(match_id, active_matches)
        matches_count = len(active_matches)
        filtered_data = {
            "match_id": data["match_id"],
            "match_mode": data["match_mode"],
            "match_elo": data["match_score"],
            "percentile": round(((matches_count - match_number)/matches_count) * 100, 2),
            "match No.": f"{match_number}/{matches_count}",
            "page No.": f"{page_number}/{math.ceil((matches_count - 8)/8 + 2)}",
            "region": convert_region(data["region_mode"]),
            "start_time": f"{start_time.strftime('%H:%M:%S')} (EEST)",
            "duration": f"{parse_match_duration(start_time)}",
            "net_worth_team_0": data["net_worth_team_0"],
            "net_worth_team_1": data["net_worth_team_1"],
            "spectators": data["spectators"],
            "players": [
                {
                    "hero": get_hero_by_id(heroes, player["hero_id"]),
                    "player_name": players_data[usteamid_to_commid(player["account_id"])]["username"],
                    "account_link": players_data[usteamid_to_commid(player["account_id"])]["user_link"],
                    "playtime": {
                        "total": game_data[0] if game_data else "N/A",
                        "2weeks": game_data[1] if game_data else "N/A"
                    }
                }
                for player in data["players"]
                for game_data in [get_user_playtime(player["account_id"])]
            ]

        }

        return filtered_data

    return "Match is not available"


def find_match_position(match_id, active_matches) -> tuple[int, int]:
    match_to_search = find_match_byid(match_id, active_matches)['match_score']
    if match_to_search:
        sorted_matches = sort_matches_byelo(active_matches, reverse=True)
        position = next(index for index, match in enumerate(sorted_matches) if match['match_id'] == match_id) + 1
        if position <= 8:
            page_number = 1 if position <= 4 else 2
        else:
            page_number = position/8 + 2

        return math.floor(page_number), position


def convert_region(region: int) -> str:
    regions = {
        0: "North America",
        1: "Europe",
        2: "Asia",
        3: "South America",
        4: "Russia",
        5: "Oceania"
    }

    return regions[region]


def convert_match_mode(match_mode: int) -> str:
    match_modes = {
        0: "Invalid",
        1: "Unranked",
        2: "PrivateLobby",
        3: "CoopBot",
        4: "Ranked",
        5: "ServerTest",
        6: "Tutorial"
    }

    return match_modes[match_mode]
