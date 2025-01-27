from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from steamfunc import get_users_data_comm

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero, get_all_heroes, get_hero_by_id


def create_inline_matches(all_matches, user_id, is_first_page) -> InlineKeyboardMarkup:
    button_match_text = []
    all_matches_count = len(all_matches)
    matches = all_matches[:10] if is_first_page else all_matches[10:]
    page_match_count = len(matches)
    match_pos = 0
    for match_data in matches:
        if match_data is not None:
            if (match_pos == page_match_count - 1 and not is_first_page) or (match_pos == page_match_count - 1 and is_first_page and all_matches_count <= 10):
                elo_gain = '-'
            elif match_pos == page_match_count - 1 and is_first_page and all_matches_count > 10:
                elo_int = match_data['match_elo'] - all_matches[10]['match_elo']
                elo_gain = get_elo_gain(elo_int)
            else:
                elo_int = match_data['match_elo'] - matches[match_pos + 1]['match_elo']
                elo_gain = get_elo_gain(elo_int)

            user_hero = get_user_hero(match_data, get_user_uid(user_id))
            user_hero = "Magician" if user_hero == "THE MAGNIFICENT SINCLAIR" else user_hero

            hero_icon = get_hero_icon(user_hero)

            button_match_text.append([InlineKeyboardButton(f"{match_data['start_time']} | {hero_icon} {user_hero} | "
                                                           f"ELO: {match_data['match_elo']} ({elo_gain})",
                                                           callback_data=f"match_{match_data['match_id']}")])

            match_pos += 1

    if all_matches_count > 10:
        controls = "▶️" if is_first_page else "◀️"
        cb_data = "page_second" if is_first_page else "page_first"
        button_match_text.append([InlineKeyboardButton(controls, callback_data=cb_data)])

    return InlineKeyboardMarkup(button_match_text)


def create_inline_leaderboard(users_avg_elo: dict):
    button_user_text = []
    user_comm_ids = [key for key in users_avg_elo.keys()]
    users_data = get_users_data_comm(user_comm_ids)
    for index, (comm_id, avg_elo) in enumerate(users_avg_elo.items(), start=0):
        user_steam_name = users_data[str(comm_id)]['username']
        pos_emoji = get_position_emoji(index)
        button_user_text.append([InlineKeyboardButton(f"{pos_emoji} {user_steam_name} - {avg_elo}",
                                 url=users_data[str(comm_id)]['user_link'])])

    return InlineKeyboardMarkup(button_user_text)


def get_elo_gain(elo_int: int) -> str:
    if elo_int < -200:
        elo_gain = '-'
    elif elo_int > 0:
        elo_gain = f"+{elo_int}"
    else:
        elo_gain = str(elo_int)

    return elo_gain


# def match_mode_choice() -> InlineKeyboardMarkup:
#     modes = [[InlineKeyboardButton("Ranked", callback_data="get_ranked_matches"),
#               InlineKeyboardButton("Unranked", callback_data="get_unranked_matches")]]
#
#     return InlineKeyboardMarkup(modes)


def create_hero_stats(heroes_wr, is_w) -> InlineKeyboardMarkup:
    hero_wr_text = []
    all_heroes = get_all_heroes()
    total_games = sum(hero["wins"] + hero["losses"] for hero in heroes_wr)
    heroes_len = len(heroes_wr)

    for hero in heroes_wr:
        hero["wr"] = round((hero["wins"] / (hero["wins"] + hero["losses"])) * 100, 2)
        hero["pr"] = round((hero["wins"] + hero["losses"]) / total_games * 12 * 100, 2)

        hero["name"] = "Magician" if hero["name"] == "THE MAGNIFICENT SINCLAIR" else hero["name"]

    heroes_wr.sort(key=lambda h: h["wr"], reverse=True) if is_w else heroes_wr.sort(key=lambda h: h["pr"], reverse=True)

    for i in range(int(heroes_len / 2)):
        hero_1_name = get_hero_by_id(all_heroes, heroes_wr[i]["hero_id"])
        hero_1_icon = get_hero_icon(hero_1_name)
        hero_2_name = get_hero_by_id(all_heroes, heroes_wr[i+int(heroes_len/2)]["hero_id"])
        hero_2_icon = get_hero_icon(hero_2_name)
        if is_w:
            hero_wr_text.append([InlineKeyboardButton(f"{hero_1_icon} {hero_1_name} - {heroes_wr[i]['wr']}%",
                                 callback_data=f"hero_{hero_1_name}_{heroes_wr[i]['wins']}_{heroes_wr[i]['losses']}_{heroes_wr[i]['wr']}_{heroes_wr[i]['pr']}"),
                                 InlineKeyboardButton(f"{hero_2_icon} {hero_2_name} - {heroes_wr[i + int(heroes_len/2)]['wr']}%",
                                 callback_data=f"hero_{hero_2_name}_{heroes_wr[i + int(heroes_len/2)]['wins']}_{heroes_wr[i + int(heroes_len/2)]['losses']}_{heroes_wr[i + int(heroes_len/2)]['wr']}_{heroes_wr[i + int(heroes_len/2)]['pr']}")])
        else:
            hero_wr_text.append([InlineKeyboardButton(f"{hero_1_icon} {hero_1_name} - {heroes_wr[i]['pr']}%",
                                                      callback_data=f"hero_{hero_1_name}_{heroes_wr[i]['wins']}_{heroes_wr[i]['losses']}_{heroes_wr[i]['wr']}_{heroes_wr[i]['pr']}"),
                                 InlineKeyboardButton(f"{hero_2_icon} {hero_2_name} - {heroes_wr[i + int(heroes_len / 2)]['pr']}%",
                                                      callback_data=f"hero_{hero_2_name}_{heroes_wr[i + int(heroes_len / 2)]['wins']}_{heroes_wr[i + int(heroes_len / 2)]['losses']}_{heroes_wr[i + int(heroes_len / 2)]['wr']}_{heroes_wr[i + int(heroes_len / 2)]['pr']}")])
    if heroes_len % 2 != 0:
        hero_name = get_hero_by_id(all_heroes, heroes_wr[-1]["hero_id"])
        hero_icon = get_hero_icon(hero_name)
        if is_w:
            hero_wr_text.append([InlineKeyboardButton(f"{hero_icon} {hero_name} - {heroes_wr[-1]['wr']}%",
                                callback_data=f"hero_{hero_name}_{heroes_wr[-1]['wins']}_{heroes_wr[-1]['losses']}_{heroes_wr[-1]['wr']}_{heroes_wr[-1]['pr']}")])
        else:
            hero_wr_text.append([InlineKeyboardButton(f"{hero_icon} {hero_name} - {heroes_wr[-1]['pr']}%",
                                callback_data=f"hero_{hero_name}_{heroes_wr[-1]['wins']}_{heroes_wr[-1]['losses']}_{heroes_wr[-1]['wr']}_{heroes_wr[-1]['pr']}")])

    return InlineKeyboardMarkup(hero_wr_text)


def lobby_rank_choice(is_w: bool) -> InlineKeyboardMarkup:
    if is_w:
        ranks = [[InlineKeyboardButton("TOP 1%", callback_data="lobby_3000_2500_w"),
                  InlineKeyboardButton("TOP 5%", callback_data="lobby_3000_2250_w"),
                  InlineKeyboardButton("All matches", callback_data="lobby_3000_1_w"),
                  InlineKeyboardButton("Your ELO", callback_data=f"w_lobby_user_elo_w")]]
    else:
        ranks = [[InlineKeyboardButton("TOP 1%", callback_data="lobby_3000_2500_p"),
                  InlineKeyboardButton("TOP 5%", callback_data="lobby_3000_2250_p"),
                  InlineKeyboardButton("All matches", callback_data="lobby_3000_1_p"),
                  InlineKeyboardButton("Your ELO", callback_data=f"lobby_user_elo_p")]]

    return InlineKeyboardMarkup(ranks)


def get_position_emoji(position: int) -> str:
    positions = {
        0: '🥇',
        1: '🥈',
        2: '🥉',
        3: '4️⃣',
        4: '5️⃣',
        5: '6️⃣',
        6: '7️⃣',
        7: '8️⃣',
        8: '9️⃣',
        9: '🔟'
    }

    return positions.get(position, '?')
