from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero, convert_match_mode


def create_inline_matches(matches, user_id) -> InlineKeyboardMarkup:
    user_uid = get_user_uid(user_id)
    button_match_text = []
    for match_data in matches:
        if match_data is not None:
            match_mode = convert_match_mode(match_data.get('match_mode', -1))
            user_hero = get_user_hero(match_data, user_uid)
            hero_icon = get_hero_icon(user_hero)
            if match_mode:
                if match_mode == "Ranked":
                    match_mode = 'R'
                elif match_mode == "Unranked":
                    match_mode = 'U'

                button_match_text.append([InlineKeyboardButton(f"[{match_mode}] | {match_data['start_time']} "
                                                               f"| {hero_icon} {user_hero} | ELO: {match_data['match_elo']}",
                                                               callback_data=f"match_{match_data['match_id']}")])
            else:
                button_match_text.append([InlineKeyboardButton(f"{match_data['start_time']} | {hero_icon} {user_hero} "
                                                               f"| ELO: {match_data['match_elo']}",
                                                               callback_data=f"match_{match_data['match_id']}")])

    return InlineKeyboardMarkup(button_match_text)
