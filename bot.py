from collections import Counter

import telegram.error
from telegram import Update, ReplyKeyboardMarkup, constants, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from dlfunc import get_active_matches, filter_match_data, get_hero_icon, get_current_minmaxelo, get_user_hero
from steamfunc import get_user_commid, commid_to_usteamid, is_steam_valid
from dbfunc import users_table_insert, is_user_registered, get_matchids_foruser, get_match_data, get_user_uid

from inline_keyboards import create_inline_matches


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


async def format_match_data(filtered_data) -> str:
    message = f"<b>Match ID:</b> {filtered_data['match_id']}\n"
    message += "===========================\n"
    message += f"<b>Match Elo:</b> {filtered_data['match_elo']}\n"
    message += f"<b>Top</b>: {round(100 - float(filtered_data['percentile']), 2)}%\n"
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
        message += "<b>Playtime</b>: \n"
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
                                        "Match duration must be <b>at least 3 minutes</b> for it to be searchable.",
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
                      "1. Your match just started. Wait 3 minutes and try again.\n" \
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
            sorted_matchids = sorted(user_matchids, reverse=True)
            user_matches = [get_match_data(match_id) for match_id in sorted_matchids]
            if user_matches:
                await update.message.reply_text(f"<b>Your {len(user_matches)} last matches</b> ⬇️",
                                                reply_markup=create_inline_matches(user_matches, user.id),
                                                parse_mode=constants.ParseMode.HTML)
            else:
                await update.message.reply_text("You have no observed matches at this moment.",
                                                reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

        else:
            await update.message.reply_text("You have no observed matches at this moment.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "📊 My Stats":
        user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        user_matchids = get_matchids_foruser(user.id)
        if user_matchids:
            user_matches = [get_match_data(match_id) for match_id in user_matchids]
            user_avgelo, avg_percentile, avg_top, fav_hero, avg_page, avg_pos = get_user_stats(user_matches, get_user_uid(user.id))
            await update.message.reply_text(construct_user_stats(user_name, user_avgelo, avg_percentile,
                                                                 avg_top, fav_hero, avg_page, avg_pos),
                                            reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True),
                                            parse_mode=constants.ParseMode.HTML)

        else:
            await update.message.reply_text("You have no observed matches at this moment.",
                                            reply_markup=ReplyKeyboardMarkup(user_menu))

    elif user_input == "My Stats" or user_input == "My Matches" or user_input == "Search LIVE game by id" or user_input == "Registration(BETA)":
        if is_user_registered(user.id):
            user_menu = [["⚔️ My Matches", "📊 My Stats"], ["🔍 Search LIVE game by id"]]
        else:
            user_menu = [["🔍 Search LIVE game by id"], ["Registration"]]

        await update.message.reply_text("We have updated buttons now!",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    elif user_input == "asdasdasd" and user.id == 648380859:
        await context.bot.send_message(648380859, get_current_minmaxelo())

    elif user_input == "hui" and user.id == 648380859:
        user_matchids = get_matchids_foruser(5160729145)

        user_matches = [get_match_data(match_id) for match_id in user_matchids]
        user_avgelo, avg_percentile, avg_top, fav_hero, avg_page, avg_pos = get_user_stats(user_matches,
                                                                                           get_user_uid(user.id))
        await update.message.reply_text(construct_user_stats(user_name, user_avgelo, avg_percentile,
                                                             avg_top, fav_hero, avg_page, avg_pos),
                                        parse_mode=constants.ParseMode.HTML)


async def callback_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("match"):
        user_id = query.message.chat.id
        match_id = int(query.data.split('_')[1])
        match_data = get_match_data(match_id)
        match_stats = create_match_stats(match_data, get_user_uid(user_id))

        await context.bot.send_message(user_id, match_stats, parse_mode=constants.ParseMode.HTML)
        await query.answer()


def construct_user_stats(user_name, user_avgelo, avg_percentile, avg_top, fav_hero, avg_page, avg_pos):
    msg = f"<b>{user_name} Stats</b>\n"
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
    user_elo = 0
    total_percentile = 0
    avg_page = 0
    avg_total_pages = 0
    avg_match_pos = 0
    avg_total_matches = 0
    user_matches_count = len(user_matches)
    heroes_list = []
    for match in user_matches:
        if match is not None:
            user_elo += match['match_elo']
            total_percentile += float(match['percentile'])
            match_position, total_matches = map(int, match['match No.'].split('/'))
            page_num, total_pages = map(int, match['page No.'].split('/'))
            avg_page += page_num
            avg_total_pages += total_pages
            avg_total_matches += total_matches
            avg_match_pos += match_position
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


def create_match_stats(match_data, user_uid):
    player_hero = get_user_hero(match_data, user_uid)
    message = "===========================\n"
    message += f"<b>Match</b> | <b>{match_data['match_id']}</b> | <b>{match_data['start_time']}</b>\n"
    message += f"<b>Region</b>: {match_data['region']}\n"
    message += "————————————————\n"
    message += f"<b>Hero</b>: {get_hero_icon(player_hero)} <b>{player_hero}</b>\n"
    message += "————————————————\n"
    message += f"<b>ELO</b>: {match_data['match_elo']}\n"
    message += f"<b>Top</b>: {round((100 - float(match_data['percentile'])), 2)}% (<b>Percentile</b>: {match_data['percentile']}%)\n"
    message += f"<b>Match №</b> {match_data['match No.']} (<b>Page №</b> {match_data['page No.']})\n"
    message += "===========================\n"

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
        await context.bot.send_message(user_id, f"Hey, we found you in a match <b>{match_id}</b>. "
                                                f"Match ELO: <b>{match_elo}</b>",
                                                parse_mode=constants.ParseMode.HTML)
    except telegram.error.BadRequest as e:
        await context.bot.send_message(648380859, f"{e} for user_id: {user_id}")

    except telegram.error.Forbidden as e:
        await context.bot.send_message(648380859, f"{e} for user_id: {user_id}")


async def end_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    await update.message.reply_text("The current operation has been canceled. "
                                    "You can start over with /start or ask for help with /faq.")
    context.user_data.clear()
    return ConversationHandler.END
