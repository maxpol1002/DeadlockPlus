from collections import Counter

from datetime import datetime
import html
import pytz

import telegram.error
from telegram import Update, ReplyKeyboardMarkup, constants, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from dlfunc import (
    get_active_matches,
    filter_match_data,
    get_hero_icon,
    get_user_hero,
    convert_match_mode,
    get_hero_winrates,
    convert_ranked_rank,
    get_hero_matchups,
    get_user_hero_stats,
    get_hero_stats_by_id
)

from steamfunc import (
    get_user_commid,
    commid_to_usteamid,
    is_steam_valid
)
from dbfunc import (
    users_table_insert,
    is_user_registered,
    get_matchids_foruser,
    get_match_data,
    get_user_uid,
    get_all_users_avg_elot
)

from inline_keyboards import (
    create_inline_matches,
    create_hero_stats,
    lobby_rank_choice,
    create_inline_leaderboard,
    create_inline_matchups, create_user_hero_stats
)


MATCH_ID = 1
REG = 2


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    if is_user_registered(user_id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

    user_menu_markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)

    await update.message.reply_text(f"Hello, <b>{user_name}</b>, with this bot you can search live game's data such as <b>official lobby MMR</b>, <b>players</b>, "
                                    f"<b>page number</b> and many other useful things.\nPress the button below to start. "
                                    f"Register so we can track your matches.\n"
                                    f"<b>(IMPORTANT: Your game must be LIVE and in the Watch tab so we can track it.)</b>",
                                    reply_markup=user_menu_markup, parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(648380859, f"{user_name} started bot")


async def users_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_avg_elo = get_all_users_avg_elot()
    sorted_users_avg_elo = dict(sorted(users_avg_elo.items(), key=lambda item: item[1], reverse=True))
    top_10_by_elo = dict(list(sorted_users_avg_elo.items())[:10])

    await update.message.reply_text("🏆 <b>TOP 10 users</b> 🏆",
                                    reply_markup=create_inline_leaderboard(top_10_by_elo),
                                    parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(648380859, f"{update.effective_user.username} opened leaderboards")


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_registered(update.effective_user.id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

    markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
    await update.message.reply_text("1. <b>How to use this bot?</b> Just follow bot instuctions and let the magic do its work :)\n"
                                    "2. <b>Why can't I find my match?</b> If you can't find your match there can be 3 reasons: "
                                    "1 - You entered wrong match id, 2 - Your match is already finished, 3 - Your match didn't reach 'watch' tab in game.\n"
                                    "3. <b>Is match MMR(elo) real?</b> Yes, this is Valve's official average lobby rating.\n"
                                    "4. <b>What is percentile?</b> It means that you are better than some % of players. "
                                    "<b>Example</b>: Percentile 90% means that you are better than 90% of players.",
                                    parse_mode=constants.ParseMode.HTML, reply_markup=markup)

    await context.bot.send_message(648380859, f"{update.effective_user.first_name} opened faq")


async def ua_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_registered(update.effective_user.id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]
    await update.message.reply_text("Join ukrainian channel! t.me/Deadlock_UA_News",
                                    reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))


async def hero_winrates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_registered(update.effective_user.id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

    await update.message.reply_text("Here you can check heroes winrates since last update (11/05)",
                                    reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))
    await update.message.reply_text("Choose lobby rank ⬇️", reply_markup=lobby_rank_choice(is_w=True))
    await context.bot.send_message(648380859, f"{update.effective_user.first_name} opened winrates")


async def hero_pickrates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_registered(update.effective_user.id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

    await update.message.reply_text("Here you can check heroes pick rates since last update (11/05)",
                                    reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))
    await update.message.reply_text("Choose lobby rank ⬇️", reply_markup=lobby_rank_choice(is_w=False))
    await context.bot.send_message(648380859, f"{update.effective_user.first_name} opened pickrates")


async def hero_matchups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_registered(update.effective_user.id):
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
    else:
        user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

    current_timestamp = int(datetime.utcnow().timestamp())
    last_patch_timestamp = 1746947220
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    current_time_eest = datetime.fromtimestamp(current_timestamp, kyiv_tz).strftime("%d/%m")
    last_patch_time_eest = datetime.fromtimestamp(last_patch_timestamp, kyiv_tz).strftime("%d/%m")

    matchups = get_hero_matchups(min_ts=last_patch_timestamp, max_ts=current_timestamp)

    await update.message.reply_text(f"Here you can check heroes matchups <b>({last_patch_time_eest} - {current_time_eest})</b>",
                                    reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True),
                                    parse_mode=constants.ParseMode.HTML)
    await update.message.reply_text("Select a hero to check matchups", reply_markup=create_inline_matchups(matchups))
    await context.bot.send_message(648380859, f"{update.effective_user.first_name} opened matchups")


def get_user_avg_elo(user_matches):
    if user_matches:
        total_elo = 0
        for match_data in user_matches:
            total_elo += match_data["match_elo"]

        return int(total_elo / len(user_matches))

    return None


async def format_match_data(filtered_data) -> str:
    ranked_badge_level = filtered_data.get("ranked_badge_level", 0)
    match_rank = convert_ranked_rank(ranked_badge_level) if ranked_badge_level != 0 else -1

    message = f"<b>Match ID:</b> {filtered_data['match_id']}\n"
    message += f"<b>Match Mode:</b> {convert_match_mode(filtered_data['match_mode'])}\n"
    message += "===========================\n"
    if match_rank != -1:
        message += f"<b>Match Rank</b>: {match_rank}\n"

    message += f"<b>Match Elo:</b> {filtered_data['match_elo']}\n"
    message += f"<b>Top:</b> {round(100 - float(filtered_data['percentile']), 2)}%\n"
    message += f"<b>Percentile:</b> {filtered_data['percentile']}%\n"
    message += f"<b>Match No:</b> {filtered_data['match No.']}\n"
    message += f"<b>Page No:</b> {filtered_data['page No.']}\n"
    message += f"<b>Spectators:</b> {filtered_data.get('spectators', 0)}\n"
    message += f"<b>Region:</b> {filtered_data['region']}\n"
    message += "===========================\n"
    message += f"<b>Start Time:</b> {filtered_data['start_time']}\n"
    message += f"<b>Duration:</b> {filtered_data['duration']}\n"
    message += f"<b>Net Worth Team 0:</b> {filtered_data['net_worth_team_0']}\n"
    message += f"<b>Net Worth Team 1:</b> {filtered_data['net_worth_team_1']}\n"
    message += "+++++++++++++++++++++++++++\n"
    message += "<b>Players:</b>\n"
    message += "+++++++++++++++++++++++++++\n"
    message += "⬇️<b>Team Amber Hand:</b>⬇️\n"
    message += "————————————————\n"
    position = 0
    for player in filtered_data['players']:
        if position == 6:
            message += "⬇️<b>Team Sapphire Flame</b>⬇️\n"
            message += "————————————————\n"

        message += f" - {get_hero_icon(player['hero'])} <b>{player['hero']}</b> (Player: <b>{player['player_name']}</b>)\n"
        message += f"Account Link: <a href='{player['account_link']}'>steam link</a>\n"
        message += "<b>Playtime:</b>\n"
        message += f"   Total - {player['playtime']['total']}"
        message += "h\n" if player['playtime']['total'] != "N/A" else "\n"
        message += f"   2 Weeks - {player['playtime']['2weeks']}"
        message += "h\n" if player['playtime']['2weeks'] != "N/A" else "\n"
        message += "————————————————\n"

        position += 1

    return message


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user = update.effective_user
    username = user.username
    user_name = user.first_name
    await context.bot.send_message(648380859, f"{user_name}({username}) typed {user_input}")

    if user_input == "🔍 Search LIVE game by id":
        context.user_data.clear()
        user_menu = [
            ["◀️ Go back"]
        ]
        await update.message.reply_text("Sure, send me your match id (you can see find in the bottom-right corner). "
                                        "Match duration must be <b>at least 1 minute</b> for it to be searchable.",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True),
                                        parse_mode=constants.ParseMode.HTML)
        return MATCH_ID

    elif user_input.startswith("🔍 Search match"):
        if context.user_data.get('match_id'):
            await update.message.reply_text(f"Searching match {context.user_data['match_id']}...",
                                            reply_markup=ReplyKeyboardRemove())
            if is_user_registered(user.id):
                user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
            else:
                user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

            await context.bot.send_message(648380859, f"{user_name} searched match {context.user_data['match_id']}")
            active_matches = get_active_matches()
            match_data = filter_match_data(context.user_data["match_id"], active_matches)
            if match_data == "Match is not available":
                msg = "Sorry, we couldn't find your match. There can be 4 reasons that explain why your match isn't appearing:\n" \
                      "1. Your match just started. Wait 1 minute and try again.\n" \
                      "2. You entered wrong match id.\n" \
                      "3. Your match is already finished.\n" \
                      "4. Your match didn't reach 'watch' tab in game."
            else:
                msg = await format_match_data(match_data)

            await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True),
                                            disable_web_page_preview=True, parse_mode=constants.ParseMode.HTML)
            context.user_data.clear()

        else:
            await update.message.reply_text("Try again. Use button to search a match.")

    elif user_input == "◀️ Go back":
        if is_user_registered(user.id):
            user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        else:
            user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

        await update.message.reply_text("You can search your live game by pressing the button below.",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "Registration":
        if not is_user_registered(user.id):
            user_menu = [
                ["◀️ Go back"]
            ]
            await update.message.reply_text("Send your steam link so we can track your matches.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))
            return REG

        else:
            user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
            await update.message.reply_text("You are already registered. We are tracking your matches.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "⚔️ My Matches":
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        user_matchids = get_matchids_foruser(user.id)
        if user_matchids:
            all_matchids = sorted(get_matchids_foruser(user.id), reverse=True)
            standart_matches = get_user_matches_bymode(all_matchids, 1)
            await context.bot.send_message(user.id, "⬇️ <b>Your matches</b> ⬇️",
                                           reply_markup=create_inline_matches(standart_matches, user.id, page_number=1),
                                           parse_mode=constants.ParseMode.HTML)

        else:
            await update.message.reply_text("You have no observed matches at this moment.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "📊 My Stats":
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        all_matchids = get_matchids_foruser(user.id)
        if all_matchids:
            all_matchids_s = sorted(all_matchids, reverse=True)
            standart_matches = get_user_matches_bymode(all_matchids_s, 1)

            if standart_matches:
                user_avgelo, avg_percentile, avg_top, fav_hero, avg_page, avg_pos = get_user_stats(standart_matches,
                                                                                                   get_user_uid(user.id))
                await update.message.reply_text(construct_user_stats("Standard", user_avgelo, avg_percentile,
                                                                     avg_top, fav_hero, avg_page, avg_pos),
                                                reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True),
                                                parse_mode=constants.ParseMode.HTML)

        else:
            await update.message.reply_text("You have no observed matches at this moment.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "My Stats" or user_input == "My Matches" or user_input == "Search LIVE game by id" or user_input == "Registration(BETA)":
        if is_user_registered(user.id):
            user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        else:
            user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

        await update.message.reply_text("We have updated buttons now!",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))


    elif user_input == "Hero Stats":
        account_id = get_user_uid(user.id)
        user_hero_stats = get_user_hero_stats(account_id)
        if user_hero_stats:
            context.user_data["user_hero_stats"] = user_hero_stats

            await update.message.reply_text("Your stats:",
                                            reply_markup=create_user_hero_stats(user_hero_stats, "matches_played", is_reverse=True),
                                            parse_mode=constants.ParseMode.HTML)


async def callback_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id
    if query.data.startswith("match"):
        match_id = int(query.data.split('_')[1])
        match_data = get_match_data(match_id)
        match_stats = create_match_stats(match_data, get_user_uid(user_id))
        delete_button = [[InlineKeyboardButton("⬅️", callback_data=f"delete_msg")]]

        await context.bot.send_message(user_id, match_stats, reply_markup=InlineKeyboardMarkup(delete_button),
                                       parse_mode=constants.ParseMode.HTML,
                                       disable_web_page_preview=True)
        await query.answer()

    elif query.data == "delete_msg":
        await update.effective_message.delete()
        await query.answer()

    elif query.data == "open_matchups":
        current_timestamp = int(datetime.utcnow().timestamp())
        last_patch_timestamp = 1739319840
        matchups = get_hero_matchups(min_ts=last_patch_timestamp, max_ts=current_timestamp)
        await query.edit_message_text("Select a hero to check matchups", reply_markup=create_inline_matchups(matchups))
        await query.answer()

    elif query.data == "nothing":
        await query.answer()

    elif query.data.startswith("lobby"):
        elo_max_q = query.data.split('_')[1]
        elo_min_q = query.data.split('_')[2]
        mode = query.data.split('_')[-1]
        lobby_type = {
            "111": "Eternus",
            "101": "Ascendant",
            "91": "Phantom",
            "81": "Oracle",
            "11": "Init-Archon",
            "0": "All ranks"
        }

        if elo_max_q.isdigit() and elo_min_q.isdigit():
            elo_max, elo_min = int(elo_max_q), int(elo_min_q)
        # else:
        #     all_matchids = get_matchids_foruser(user_id)
        #     if all_matchids:
        #         standard_matches = get_user_matches_bymode(all_matchids, 1)
        #         if standard_matches:
        #             user_avg_elo = get_user_avg_elo(standard_matches)
        #             elo_max = user_avg_elo + 200 if user_avg_elo else 0
        #             elo_min = user_avg_elo - 200 if user_avg_elo else 0
        #         else:
        #             elo_max = 0
        #             elo_min = 0
        #     else:
        #         elo_max = 0
        #         elo_min = 0

        current_timestamp = int(datetime.utcnow().timestamp())
        last_patch_timestamp = 1739319840
        kyiv_tz = pytz.timezone('Europe/Kyiv')
        current_time_eest = datetime.fromtimestamp(current_timestamp, kyiv_tz).strftime("%d/%m")
        last_patch_time_eest = datetime.fromtimestamp(last_patch_timestamp, kyiv_tz).strftime("%d/%m")

        hero_wrs = get_hero_winrates(elo_min, elo_max, last_patch_timestamp, current_timestamp)
        if hero_wrs and mode == 'w':
            await context.bot.send_message(user_id, f"Heroes winrates <b>({last_patch_time_eest} - {current_time_eest})</b> "
                                                    f"- <b>{lobby_type[elo_min_q]}</b>",
                                                    reply_markup=create_hero_stats(hero_wrs, is_w=True),
                                                    parse_mode=constants.ParseMode.HTML)

        elif mode == 'p' and len(hero_wrs) == 26:
            await context.bot.send_message(user_id,
                                           f"Heroes pick rates <b>({last_patch_time_eest} - {current_time_eest})</b> "
                                           f"- <b>{lobby_type[elo_min_q]}</b>",
                                           reply_markup=create_hero_stats(hero_wrs, is_w=False),
                                           parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(user_id, "No data available now, try again later.")

        await query.answer()

    elif query.data.startswith("hero"):
        hero_data = query.data.split('_')
        hero_name = hero_data[1]
        hero_wins = int(hero_data[2])
        hero_losses = int(hero_data[3])
        hero_winrate = hero_data[4]
        hero_pickrate = hero_data[5]
        hero_icon = get_hero_icon(hero_name)

        message = f"————————————————\n"
        message += f"{hero_icon} <b>{hero_name}</b>\n"
        message += f"————————————————\n"
        message += f"<b>Winrate</b>: {hero_winrate}%\n"
        message += f"<b>Pickrate</b>: {hero_pickrate}%\n"
        message += f"<b>Total games</b>: {hero_wins + hero_losses}\n"
        message += f"<b>Wins</b>: {hero_wins}\n"
        message += f"<b>Losses</b>: {hero_losses}\n"
        message += f"————————————————\n"

        await context.bot.send_message(user_id, message, parse_mode=constants.ParseMode.HTML)

        await query.answer()

    elif query.data.startswith("page"):
        page_number = int(query.data.split("_")[1])
        all_matchids = sorted(get_matchids_foruser(query.from_user.id), reverse=True)
        standart_matches = get_user_matches_bymode(all_matchids, 1)
        try:
            await query.edit_message_reply_markup(create_inline_matches(standart_matches, query.from_user.id,
                                                                        page_number=page_number))
        except telegram.error.BadRequest:
            pass

        await query.answer()

    elif query.data.startswith("hmatchups"):
        hero_id = int(query.data.split("_")[1])
        current_timestamp = int(datetime.utcnow().timestamp())
        last_patch_timestamp = 1739319840
        matchups = get_hero_matchups(min_ts=last_patch_timestamp, max_ts=current_timestamp)
        await query.edit_message_text("Matchups ⬇️", reply_markup=create_inline_matchups(matchups, hero_id))

        await query.answer()

    elif query.data.startswith("hem"):
        matchup_data = query.data.split('_')
        matchup_hero_name = matchup_data[1]
        matchup_hero_wr = float(matchup_data[2])
        matchup_hero_wins = int(matchup_data[3])
        matchup_hero_losses = int(matchup_data[4])
        chosen_hero_name = matchup_data[5]

        matchup_hero_icon = get_hero_icon(matchup_hero_name)
        chosen_hero_icon = get_hero_icon(chosen_hero_name)

        message = f"————————————————\n"
        message += f"{chosen_hero_icon} <b>{chosen_hero_name}</b> VS <b>{matchup_hero_name}</b> {matchup_hero_icon}\n"
        message += f"————————————————\n"
        message += f"<b>Winrate</b>: {matchup_hero_wr}%\n"
        message += f"<b>Total games</b>: {matchup_hero_wins + matchup_hero_losses}\n"
        message += f"<b>Wins</b>: {matchup_hero_wins}\n"
        message += f"<b>Losses</b>: {matchup_hero_losses}\n"
        message += f"————————————————\n"

        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌", callback_data=f"delete_msg")]])

        await context.bot.send_message(user_id, message, reply_markup=markup, parse_mode=constants.ParseMode.HTML)
        await query.answer()

    elif query.data.startswith("uhs-sort"):
        _, _, sort_value, sort_dir = query.data.split('-')
        is_reverse = True if sort_dir == "desc" else False

        try:
            await query.edit_message_reply_markup(create_user_hero_stats(context.user_data["user_hero_stats"],
                                                                         sort_value,
                                                                         is_reverse=is_reverse))

        except telegram.error.BadRequest:
            pass

        await query.answer()

    elif query.data.startswith("uhs_hero"):
        _, _, hero_id = query.data.split('_')
        user_hero_stats = context.user_data["user_hero_stats"]
        hero_data = get_hero_stats_by_id(user_hero_stats, hero_id)

        await context.bot.send_message(user_id, f"{hero_id}")

        msg = await construct_hero_stats(hero_data)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌", callback_data=f"delete_msg")]])

        await context.bot.send_message(user_id, msg, reply_markup=markup, parse_mode=constants.ParseMode.HTML)

        await query.answer()


def get_user_matches_bymode(all_matchids, match_mode):
    user_matches = []
    for match_id in all_matchids:
        match_data = get_match_data(match_id)
        if match_data and match_data['match_mode'] == match_mode:
            user_matches.append(match_data)

    return user_matches


def construct_user_stats(match_mode, user_avgelo, avg_percentile, avg_top, fav_hero, avg_page, avg_pos):
    msg = f"<b>{match_mode} Stats</b>\n"
    msg += "————————————————\n"
    msg += f"<b>ELO</b>: {user_avgelo}\n"
    msg += f"<b>Top</b>: {avg_top}%\n"
    msg += f"<b>Percentile</b>: {avg_percentile}%\n"
    msg += "————————————————\n"
    msg += f"<b>Average match position</b>: {avg_pos}\n"
    msg += f"<b>Average match page</b>: {avg_page}\n"
    msg += "————————————————\n"
    msg += f"<b>Favorite hero</b>: {get_hero_icon(fav_hero)} <b>{fav_hero}</b>\n"
    msg += "————————————————\n"

    return msg


def get_user_stats(user_matches, user_uid):
    max_elo = max(match['match_elo'] for match in user_matches if match is not None)
    user_elo = 0
    total_percentile = 0.0
    avg_page = 0
    avg_total_pages = 0
    avg_match_pos = 0
    avg_total_matches = 0
    user_matches_count = 0
    heroes_list = []
    for match in user_matches:
        if match is not None and max_elo - match['match_elo'] <= 300:
            user_elo += match['match_elo']
            total_percentile += match['percentile']
            match_position, total_matches = map(int, match['match No.'].split('/'))
            page_num, total_pages = map(int, match['page No.'].split('/'))
            avg_page += page_num
            avg_total_pages += total_pages
            avg_total_matches += total_matches
            avg_match_pos += match_position
            user_matches_count += 1
            for player in match['players']:
                if player['account_id'] == user_uid:
                    heroes_list.append(player['hero'])

    user_avgelo = round(user_elo/user_matches_count)
    avg_percentile = round(total_percentile/user_matches_count, 2)
    avg_top = str(round(100 - avg_percentile, 2))
    fav_hero = Counter(heroes_list).most_common(1)[0][0]
    avg_page = round(avg_page / user_matches_count)
    avg_total_pages = round(avg_total_pages / user_matches_count)
    avg_match_pos = round(avg_match_pos / user_matches_count)
    avg_total_matches = round(avg_total_matches / user_matches_count)
    page_stat = f"{avg_page}/{avg_total_pages}"
    matchpos_stat = f"{avg_match_pos}/{avg_total_matches}"

    return user_avgelo, avg_percentile, avg_top, fav_hero, page_stat, matchpos_stat


def create_match_stats(match_data, user_uid) -> str:
    player_hero = get_user_hero(match_data, user_uid)
    message = f"<b>Match</b> | <b>{match_data['match_id']}</b> | <b>{match_data['start_time']}</b>\n"
    message += "————————————————\n"
    message += f"<b>Hero</b>: {get_hero_icon(player_hero)} <b>{player_hero}</b>\n"
    message += "————————————————\n"
    message += f"<b>ELO</b>: {match_data['match_elo']}\n"
    message += f"<b>Top</b>: {round((100 - float(match_data['percentile'])), 2)}% (<b>Percentile</b>: {match_data['percentile']}%)\n"
    message += f"<b>Match №</b> {match_data['match No.']} (<b>Page №</b> {match_data['page No.']})\n"
    message += "————————————————\n"
    message += f"<b>Mode</b>: {convert_match_mode(match_data['match_mode'])}\n"
    message += f"<b>Region</b>: {match_data['region']}\n"
    message += "————————————————\n"
    message += "      ⬇️ <b>Team Amber Hand</b> ⬇️\n"
    message += "————————————————\n"
    position = 0
    for player in match_data['players']:
        if position == 6:
            message += "————————————————\n"
            message += "    ⬇️ <b>Team Sapphire Flame</b> ⬇️\n"
            message += "————————————————\n"

        player_name = html.escape(player['player_name']) if player['player_name'].isprintable() else "invisible"
        if user_uid == player['account_id']:
            message += f"{get_hero_icon(player['hero'])} <b><u>{player['hero']}</u></b> (<a href='{player['account_link']}'><b>{player_name}</b></a>)\n"
        else:
            message += f"{get_hero_icon(player['hero'])} {player['hero']} (<a href='{player['account_link']}'><b>{player_name}</b></a>)\n"

        position += 1

    return message


async def construct_hero_stats(hero_data) -> str:
    if not hero_data:
        message = "No available data at this moment. Try again later."
    else:
        hero_icon = get_hero_icon(hero_data['hero_name'])
        message = f"————————————————\n"
        message += f"{hero_icon} <b>{hero_data['hero_name']}</b>\n"
        message += f"————————————————\n"
        message += f"<b>Winrate</b>: {hero_data['wr']}%\n"
        message += f"<b>Total games</b>: {hero_data['matches_played']}\n"
        message += f"<b>Wins</b>: {hero_data['wins']}\n"
        message += f"<b>Losses</b>: {hero_data['matches_played'] - hero_data['wins']}\n"
        message += f"————————————————\n"
        message += f"Kills: {hero_data['kills']}\n"
        message += f"Deaths: {hero_data['deaths']}\n"
        message += f"Assists: {hero_data['assists']}\n"
        message += f"————————————————\n"
        message += f"Accuracy: {hero_data['accuracy']}%\n"
        message += f"Crit Rate: {hero_data['crit_shot_rate']}%\n"
        message += f"SPM: {hero_data['networth_per_min']}\n"

    return message


async def registration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_link_input = update.message.text
    if user_link_input == "◀️ Go back":
        user_menu = [
            ["🔍 Search LIVE game by id"], ["Registration"]
        ]
        await update.message.reply_text("You should register so we can track your matches.",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

        return ConversationHandler.END

    if not is_steam_valid(user_link_input) or get_user_commid(user_link_input) is None:
        await context.bot.send_message(update.effective_user.id, "Wrong steam link, try again.")
        return REG

    else:
        user_commid = get_user_commid(user_link_input)
        if user_commid is not None:
            user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
            users_table_insert(user.id, user.first_name, user.username, user_link_input, commid_to_usteamid(user_commid), user_commid)
            await context.bot.send_message(update.effective_user.id, "Thanks for registation! Now we are tracking your matches.",
                                           reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

            return ConversationHandler.END


async def match_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        match_id_input = update.message.text
        if "match_id" not in context.user_data:
            if match_id_input == "◀️ Go back":
                if is_user_registered(update.effective_user.id):
                    user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
                else:
                    user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

                await update.message.reply_text("You can search your live game by pressing button below.",
                                                reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

                return ConversationHandler.END

            elif not match_id_input.isdigit() or len(match_id_input) != 8:
                await context.bot.send_message(update.effective_user.id, "Wrong match id, try again.")
                return MATCH_ID

        context.user_data["match_id"] = int(match_id_input)
        user_menu = [
            ["◀️ Go back", f"🔍 Search match {match_id_input}"]
        ]
        await context.bot.send_message(update.effective_user.id, "Press the button below to search.",
                                       reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

        return ConversationHandler.END


async def notify_user(user_id, match_id, match_elo, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = f"Hey, we found you in a match <b>{match_id}</b>.\n"
        msg += f"Match ELO: <b>{match_elo}</b>"
        await context.bot.send_message(user_id, msg, parse_mode=constants.ParseMode.HTML)

    except telegram.error.BadRequest as e:
        await context.bot.send_message(648380859, f"{e} for user_id: {user_id}")

    except telegram.error.Forbidden as e:
        await context.bot.send_message(648380859, f"{e} for user_id: {user_id}")


async def end_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    await update.message.reply_text("The current operation has been canceled. "
                                    "You can start over with /start or ask for help with /faq.")
    context.user_data.clear()
    return ConversationHandler.END
