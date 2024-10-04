import os

import requests


def usteamid_to_commid(account_id):
    usteamid = f'[U:1:{account_id}]'
    for ch in ['[', ']']:
        if ch in usteamid:
            usteamid = usteamid.replace(ch, '')

    usteamid_split = usteamid.split(':')
    commid = int(usteamid_split[2]) + 76561197960265728

    return str(commid)


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
