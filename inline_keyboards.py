from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero, convert_match_mode


def create_inline_matches(matches, user_id) -> InlineKeyboardMarkup:
    button_match_text = []
    tmp_elo = None
    for match_data in matches:
        if match_data is not None:
            if tmp_elo is None:
                elo_gain = '-'
            else:
                elo_gain = str(match_data['match_elo'] - tmp_elo)

            tmp_elo = match_data['match_elo']
            match_mode = convert_match_mode(match_data['match_mode'])
            user_hero = get_user_hero(match_data, get_user_uid(user_id))
            hero_icon = get_hero_icon(user_hero)
            if match_mode == "Ranked":
                match_mode = 'R'
            elif match_mode == "Unranked":
                match_mode = 'U'

            button_match_text.append([InlineKeyboardButton(f"[{match_mode}] {match_data['start_time']} "
                                                           f"| {hero_icon} {user_hero} | ELO: {match_data['match_elo']}",
                                                           callback_data=f"match_{match_data['match_id']}")])

    return InlineKeyboardMarkup(button_match_text)


def match_mode_choice() -> InlineKeyboardMarkup:
    modes = [[InlineKeyboardButton("Ranked", callback_data="get_ranked_matches"),
              InlineKeyboardButton("Unranked", callback_data="get_unranked_matches")]]

    return InlineKeyboardMarkup(modes)
