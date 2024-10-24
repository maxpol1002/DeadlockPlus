import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero, get_all_heroes, get_hero_by_id


def create_inline_matches(matches, user_id) -> InlineKeyboardMarkup:
    button_match_text = []
    match_pos = 0
    for match_data in matches:
        if match_data is not None:
            if match_pos == len(matches) - 1:
                elo_gain = '-'
            else:
                elo_int = match_data['match_elo'] - matches[match_pos + 1]['match_elo']
                if elo_int < -250:
                    elo_gain = '-'
                elif elo_int > 0:
                    elo_gain = f"+{elo_int}"
                else:
                    elo_gain = str(elo_int)

            user_hero = get_user_hero(match_data, get_user_uid(user_id))
            hero_icon = get_hero_icon(user_hero)

            button_match_text.append([InlineKeyboardButton(f"{match_data['start_time']} | {hero_icon} {user_hero} | "
                                                           f"ELO: {match_data['match_elo']} ({elo_gain})",
                                                           callback_data=f"match_{match_data['match_id']}")])

            match_pos += 1

    return InlineKeyboardMarkup(button_match_text)


def match_mode_choice() -> InlineKeyboardMarkup:
    modes = [[InlineKeyboardButton("Ranked", callback_data="get_ranked_matches"),
              InlineKeyboardButton("Unranked", callback_data="get_unranked_matches")]]

    return InlineKeyboardMarkup(modes)


def create_hero_winrates(heroes_wr) -> InlineKeyboardMarkup:
    hero_wr_text = []
    all_heroes = get_all_heroes()
    for hero in heroes_wr:
        hero["wr"] = round((hero["wins"] / (hero["wins"] + hero["losses"])) * 100, 2)

    heroes_wr.sort(key=lambda h: h["wr"], reverse=True)
    heroes_len = len(heroes_wr)

    for i in range(int(heroes_len / 2)):
        hero_1_name = get_hero_by_id(all_heroes, heroes_wr[i]["hero_id"])
        hero_1_icon = get_hero_icon(hero_1_name)
        hero_2_name = get_hero_by_id(all_heroes, heroes_wr[i+int(heroes_len/2)]["hero_id"])
        hero_2_icon = get_hero_icon(hero_2_name)
        hero_wr_text.append([InlineKeyboardButton(f"{hero_1_icon} {hero_1_name} - {heroes_wr[i]['wr']}%",
                                                  callback_data="do_nothing"),
                             InlineKeyboardButton(f"{hero_2_icon} {hero_2_name} - {heroes_wr[i + int(heroes_len/2)]['wr']}%",
                                                  callback_data="do_nothing")])

    if heroes_len % 2 != 0:
        hero_name = get_hero_by_id(all_heroes, heroes_wr[-1])
        hero_icon = get_hero_icon(hero_name)
        hero_wr_text.append([InlineKeyboardButton(f"{hero_icon} {hero_name} - {heroes_wr[-1]['wr']}%",
                                                  callback_data="do_nothing")])

    return InlineKeyboardMarkup(hero_wr_text)


def lobby_rank_choice() -> InlineKeyboardMarkup:
    ranks = [[InlineKeyboardButton("TOP 1%", callback_data="lobby_2800_2300"),
              InlineKeyboardButton("TOP 5%", callback_data="lobby_2800_1500"),
              InlineKeyboardButton("All matches", callback_data="lobby_2800_1"),
              InlineKeyboardButton("Your ELO", callback_data=f"lobby_user_elo")]]

    return InlineKeyboardMarkup(ranks)

