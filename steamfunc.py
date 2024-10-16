import os
import re
import requests


def usteamid_to_commid(account_id):
    commid = int(account_id) + 76561197960265728
    return str(commid)


def commid_to_usteamid(commid):
    return int(commid) - 76561197960265728


def is_steam_valid(link):
    steam_link_regex = r"^https://steamcommunity\.com/(id|profiles)/.*$"
    if not re.match(steam_link_regex, link):
        return False

    return True


def get_user_commid(steam_link):
    commid = None
    if "/id/" in steam_link:
        custom_name = steam_link.split('/id/')[1].replace('/', '')
        url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={os.getenv('skey')}&vanityurl={custom_name}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['response']['success'] == 1:
                commid = data['response']['steamid']

    elif "/profiles/" in steam_link:
        commid = steam_link.split('/profiles/')[1].replace('/', '')

    return commid


def get_user_playtime(account_id):
    commid = usteamid_to_commid(account_id)
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={os.getenv('skey')}&steamid={commid}&format=json"
    response = requests.get(url)

    if response.status_code == 200:
        games_data = response.json().get('response', {}).get('games', [])
        if games_data:
            for game in games_data:
                if game.get('appid') == 1422450:
                    if game.get('playtime_forever') != 0:
                        return round(game.get('playtime_forever', 0) / 60, 1), round(game.get('playtime_2weeks', 0) / 60, 1)

        return "N/A", "N/A"

    return "N/A", "N/A"


def get_users_data(acc_ids: list):
    commids = [usteamid_to_commid(accid) for accid in acc_ids]
    commids_str = '.'.join(str(commid) for commid in commids)
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={os.getenv('skey')}&steamids={commids_str}"
    response = requests.get(url)
    data = response.json()['response']['players']
    users_data = {
        player["steamid"]: {
            "username": player["personaname"],
            "user_link": player["profileurl"]
        }
        for player in data
    }

    return users_data
