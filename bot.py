import logging

from telegram import Update, ReplyKeyboardMarkup, constants, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from dlfunc import get_active_matches, filter_match_data


# logging.basicConfig(
#     filename='bot.logs',
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

MATCH_ID = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_menu = [
        ["Search LIVE game by id"]
    ]
    user_menu_markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    await update.message.reply_text(f"Hello, <b>{user_name}</b>, with this bot you can search live game's data such as <b>official lobby MMR</b>, <b>players</b>, "
                                    f"<b>page number</b> and many other useful things.\nPress the button below to start.\n"
                                    f"<b>(IMPORTANT: Your game must be LIVE and in the Watch tab so we can track it.)</b>",
                                    reply_markup=user_menu_markup, parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(648380859, f"{user_name} started bot")


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1. <b>How to use this bot?</b> Just follow bot instuctions and let the magic do its work :)\n"
                                    "2. <b>Why can't I find my match?</b> If you can't find your match there can be 3 reasons: "
                                    "1 - You entered wrong match id, 2 - Your match is already finished, 3 - Your match didn't reach 'watch' tab in game.\n"
                                    "3. <b>Is match MMR(elo) real?</b> Yes, this is Valve's official average lobby rating.\n"
                                    "4. <b>What is percentile?</b> It means that you are better than some % of players. "
                                    "<b>Example</b>: Percentile 90% means that you are better than 90% of players.",
                                    parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(648380859, f"{update.effective_user.first_name} opened faq")


def get_hero_icon(hero_name: str):
    hero_icons = {
        "Abrams": "😈",
        "Bebop": "🤖",
        "Dynamo": "❎",
        "Grey Talon": "🏹",
        "Haze": "😶‍🌫️",
        "Infernus": "🔥",
        "Ivy": "🗿",
        "Kelvin": "🥶",
        "Lady Geist": "🔫",
        "Lash": "👨‍🦰",
        "McGinnis": "🚀",
        "Mirage": "🌪",
        "Mo & Krill": "🐽",
        "Paradox": "🔄",
        "Pocket": "💼",
        "Seven": "⚡️",
        "Shiv": "🩸",
        "Vindicta": "🎯",
        "Viscous": "🟢",
        "Warden": "👮‍♂️",
        "Wraith": "🃏",
        "Yamato": "⛩"
    }

    return hero_icons.get(hero_name, "")


async def format_match_data(filtered_data):
    message = f"<b>Match ID:</b> {filtered_data['match_id']}\n"
    message += "===========================\n"
    message += f"<b>Match Elo:</b> {filtered_data['match_elo']}\n"
    message += f"<b>Percentile:</b> {filtered_data['percentile']}\n"
    message += f"<b>Match No:</b> {filtered_data['match No.']}\n"
    message += f"<b>Page No:</b> {filtered_data['page No.']}\n"
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
    await context.bot.send_message(648380859, f"{user_name} typed {user_input}")

    if user_input == "Search LIVE game by id":
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
        await update.message.reply_text(f"Searching match {context.user_data['match_id']}...",
                                        reply_markup=ReplyKeyboardRemove())
        user_menu = [
            ["Search LIVE game by id"]
        ]
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

    elif user_input == "◀️ Go back":
        user_menu = [
            ["Search LIVE game by id"]
        ]
        await update.message.reply_text("You can search your live game by pressing the button below.",
                                        reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))


async def match_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match_id_input = update.message.text
    if "match_id" not in context.user_data:
        if match_id_input == "◀️ Go back":
            user_menu = [
                ["Search LIVE game by id"]
            ]
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


async def end_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The current operation has been canceled. "
                                    "You can start over with /start or ask for help with /faq.")
    context.user_data.clear()
    return ConversationHandler.END
