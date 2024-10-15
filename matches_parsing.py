from datetime import datetime
import math
import pytz

from telegram.ext import ContextTypes

from dlfunc import (
    get_active_matches,
    get_all_heroes,
    convert_region,
    find_match_position,
    get_hero_by_id,
)

from dbfunc import (
    get_users_uids,
    insert_users_matches,
    update_user_matches,
    get_user_matchcount,
    remove_user_fmatch,
    if_any_user_has_match,
    if_user_has_match,
    delete_match,
    get_user_id
)

from steamfunc import (
    get_users_data,
    usteamid_to_commid
)

from bot import notify_user


def parse_users_matches(user_uids: list, active_matches: list, context: ContextTypes.DEFAULT_TYPE):
    found_matches = []
    user_uids_set = set(user_uids)
    for match in active_matches:
        for player in match['players']:
            if player['account_id'] in user_uids_set and not if_user_has_match(player['account_id'], match['match_id']):
                found_matches.append(match)
                await notify_user(get_user_id(player['account_id']), match['match_id'], context)

                if get_user_matchcount(player['account_id']) == 10:
                    removed_match_id = remove_user_fmatch(player['account_id'])
                    if not if_any_user_has_match(removed_match_id):
                        delete_match(match['match_id'])

                update_user_matches(player['account_id'], match['match_id'])

    return found_matches


def filter_data(match_data, active_matches):
    heroes = get_all_heroes()
    players_accids = [player["account_id"] for player in match_data["players"]]
    players_data = get_users_data(players_accids)
    page_number, match_number = find_match_position(match_data['match_id'], active_matches)
    matches_count = len(active_matches)
    filtered_data = {
        "match_id": match_data["match_id"],
        "match_elo": match_data["match_score"],
        "percentile": round(((matches_count - match_number)/matches_count) * 100, 2),
        "match No.": f"{match_number}/{matches_count}",
        "page No.": f"{page_number}/{math.ceil((matches_count - 8)/8 + 2)}",
        "region": convert_region(match_data["region_mode"]),
        "start_time": f"{get_match_datetime(match_data['start_time'])}",
        "spectators:": match_data.get('spectators'),
        "players": [
            {
                "hero": get_hero_by_id(heroes, player["hero_id"]),
                "account_id": player["account_id"],
                "player_name": players_data[usteamid_to_commid(player["account_id"])]["username"],
                "account_link": players_data[usteamid_to_commid(player["account_id"])]["user_link"],
            }
            for player in match_data["players"]
        ]

    }

    return filtered_data


async def parse_matches_job(context: ContextTypes.DEFAULT_TYPE):
    active_matches = get_active_matches()
    users_uids = get_users_uids()
    users_matches = parse_users_matches(users_uids, active_matches, context)
    if users_matches:
        filtered_match_data = [filter_data(match, active_matches) for match in users_matches]
        insert_users_matches(filtered_match_data)


async def start_job(context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_repeating(parse_matches_job, interval=180, first=0)


def get_match_datetime(timestamp):
    tz = pytz.timezone('Europe/Kyiv')
    utc_time = datetime.utcfromtimestamp(timestamp)
    kyiv_time = pytz.utc.localize(utc_time).astimezone(tz)

    formatted_time = kyiv_time.strftime('%d/%m %H:%M')

    return formatted_time

