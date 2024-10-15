from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero


def create_inline_matches(matches, user_id) -> InlineKeyboardMarkup:
    user_uid = get_user_uid(user_id)
    button_match_text = []
    for match_data in matches:
        user_hero = get_user_hero(match_data, user_uid)
        hero_icon = get_hero_icon(user_hero)
        button_match_text.append([InlineKeyboardButton(f"{match_data['start_time']} | {hero_icon} {user_hero} | ELO: {match_data['match_elo']}",
                                                       callback_data=f"match_{match_data['match_id']}")])

    return InlineKeyboardMarkup(button_match_text)
