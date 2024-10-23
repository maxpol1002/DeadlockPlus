from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from dbfunc import get_user_uid

from dlfunc import get_hero_icon, get_user_hero


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
