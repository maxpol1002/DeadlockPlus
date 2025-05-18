import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from steamfunc import get_users_data

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero, get_all_heroes, get_hero_by_id


def create_inline_matches(all_matches, user_id, page_number) -> InlineKeyboardMarkup:
    button_match_text = []
    all_matches_count = len(all_matches)
    pages_count = math.ceil(all_matches_count / 10)
    matches = all_matches[:10] if page_number == 1 else all_matches[(page_number * 10) - 10:(page_number * 10)]
    page_match_count = len(matches)
    match_pos = 0
    for match_data in matches:
        if match_data is not None:
            if match_data["match_id"] == all_matches[-1]["match_id"]:
                elo_gain = '-'
            elif match_pos == page_match_count - 1 and all_matches_count > 10:
                elo_int = match_data['match_elo'] - all_matches[page_number * 10]['match_elo']
                elo_gain = get_elo_gain(elo_int)
            else:
                elo_int = match_data['match_elo'] - matches[match_pos + 1]['match_elo']
                elo_gain = get_elo_gain(elo_int)

            user_hero = get_user_hero(match_data, get_user_uid(user_id))
            user_hero = "Sinclair" if user_hero == "THE MAGNIFICENT SINCLAIR" else user_hero

            hero_icon = get_hero_icon(user_hero)

            button_match_text.append([InlineKeyboardButton(f"{match_data['start_time']} | {hero_icon} {user_hero} | "
                                                           f"ELO: {match_data['match_elo']} ({elo_gain})",
                                                           callback_data=f"match_{match_data['match_id']}")])

            match_pos += 1

    controls = []
    for i in range(1, pages_count + 1):
        page_text = f"· {i} ·" if i == page_number else str(i)
        controls.append(InlineKeyboardButton(page_text, callback_data=f"page_{i}"))

    button_match_text.append(controls)

    return InlineKeyboardMarkup(button_match_text)


def create_inline_leaderboard(users_avg_elo: dict):
    button_user_text = []
    user_comm_ids = [key for key in users_avg_elo.keys()]
    users_data = get_users_data(user_comm_ids)
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


def create_inline_matchups(hero_matchups, selected_hero_id: int | None = None) -> InlineKeyboardMarkup:
    all_heroes = get_all_heroes()
    hero_button_text = []
    buttons_row = []

    if not selected_hero_id:
        seen_hero_ids = set()
        unique_hero_data = []

        for hero_data in hero_matchups:
            if hero_data["hero_id"] not in seen_hero_ids:
                seen_hero_ids.add(hero_data["hero_id"])
                unique_hero_data.append(hero_data)

        for hero in unique_hero_data:
            hero_name = get_hero_by_id(all_heroes, hero["hero_id"])
            hero_icon = get_hero_icon(hero_name)
            buttons_row.append(InlineKeyboardButton(f"{hero_icon} {hero_name}", callback_data=f"hmatchups_{hero['hero_id']}"))

            if len(buttons_row) == 3:
                hero_button_text.append(buttons_row)
                buttons_row = []

        if buttons_row:
            hero_button_text.append(buttons_row)

    else:
        chosen_hero_name = get_hero_by_id(all_heroes, selected_hero_id)
        chosen_hero_icon = get_hero_icon(chosen_hero_name)
        hero_button_text.append([InlineKeyboardButton(f"{chosen_hero_icon} {chosen_hero_name} ✅",
                                                      callback_data="nothing")])

        matchups = get_matchups_for_hero(hero_matchups, selected_hero_id)
        for matchup in matchups:
            hero_name = get_hero_by_id(all_heroes, matchup["enemy_hero_id"])
            hero_icon = get_hero_icon(hero_name)
            buttons_row.append(InlineKeyboardButton(f"{hero_icon} {hero_name} - {matchup['wr']}%",
                                                    callback_data=f"hem_{hero_name}_{matchup['wr']}_{matchup['wins']}_{matchup['losses']}_{chosen_hero_name}"))

            if len(buttons_row) == 2:
                hero_button_text.append(buttons_row)
                buttons_row = []

        if buttons_row:
            hero_button_text.append(buttons_row)

        hero_button_text.append([InlineKeyboardButton("⬅️", callback_data="open_matchups")])

    return InlineKeyboardMarkup(hero_button_text)


def create_user_hero_stats(user_hero_stats, sort_value, is_reverse) -> InlineKeyboardMarkup:
    columns_names = ["Name", "Matches", "WR", "K/D"]
    column_buttons = []
    sort_indicator = "🔽" if is_reverse else "🔼"
    sort_values = {
        "Name": "name",
        "Matches": "matches_played",
        "WR": "winrate",
        "K/D": "kd"
    }

    user_hero_stats_s = sorted(user_hero_stats, key=lambda x: x[sort_value], reverse=is_reverse)

    tmp = []

    for column_name in columns_names:
        button_text = f"{sort_indicator} {column_name}" if sort_values[column_name] == sort_value else column_name
        next_dir = "desc" if sort_values["column_name"] == sort_value else "asc"
        cb_data = f"uhs-sort-{sort_values[column_name]}-{next_dir}" if sort_value != "name" else "nothing"
        tmp.append(InlineKeyboardButton(text=button_text, callback_data=cb_data))

    column_buttons.append(tmp)

    all_heroes = get_all_heroes()
    buttons_row = []

    for hero in user_hero_stats_s:
        hero_name = get_hero_by_id(all_heroes, hero["hero_id"])
        hero_icon = get_hero_icon(hero_name)

        buttons_row.append(InlineKeyboardButton(f"{hero_icon} {hero_name}", callback_data="sdaf"))
        buttons_row.append(InlineKeyboardButton(f"{hero['matches_played']}", callback_data="nothing"))
        buttons_row.append(InlineKeyboardButton(f"{hero['winrate']}%", callback_data="nothing"))
        buttons_row.append(InlineKeyboardButton(f"{hero['kd']}", callback_data="nothing"))

        column_buttons.append(buttons_row)
        buttons_row = []

    return InlineKeyboardMarkup(column_buttons)



def lobby_rank_choice(is_w: bool) -> InlineKeyboardMarkup:
    if is_w:
        ranks = [[InlineKeyboardButton("🌍 All ranks", callback_data="lobby_116_0_w"),
                  InlineKeyboardButton("🩵 Eternus", callback_data="lobby_116_111_w"),
                  InlineKeyboardButton("☀️ Ascendant", callback_data="lobby_106_101_w")],

                 [InlineKeyboardButton("💀 Phantom", callback_data=f"lobby_96_91_w"),
                  InlineKeyboardButton("🐐 Oracle", callback_data=f"lobby_86_81_w"),
                  InlineKeyboardButton("📶 Archon-Init", callback_data=f"lobby_76_11_w")]
                 ]
    else:
        ranks = [[InlineKeyboardButton("🌍 All ranks", callback_data="lobby_116_0_p"),
                  InlineKeyboardButton("🩵 Eternus", callback_data="lobby_116_111_p"),
                  InlineKeyboardButton("☀️ Ascendant", callback_data="lobby_106_101_p")],

                 [InlineKeyboardButton("💀 Phantom", callback_data=f"lobby_96_91_p"),
                  InlineKeyboardButton("🐐 Oracle", callback_data=f"lobby_86_81_p"),
                  InlineKeyboardButton("📶 Archon-Init", callback_data=f"lobby_76_11_p")]
                 ]

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


def get_matchups_for_hero(all_matchups_data, selected_hero_id):
    hero_matchups_data = []
    for matchup in all_matchups_data:
        if matchup["hero_id"] == selected_hero_id:
            matchup["losses"] = matchup["matches_played"] - matchup["wins"]
            matchup["wr"] = round((matchup["wins"] / matchup["matches_played"]) * 100, 2) if matchup["matches_played"] > 0 else 0
            hero_matchups_data.append(matchup)

    if hero_matchups_data:
        return sorted(hero_matchups_data, key=lambda x: x["wr"], reverse=True)

    return None
