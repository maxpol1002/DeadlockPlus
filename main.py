import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)

from bot import (
    message_handler,
    callback_data_handler,
    registration_handler,
    match_id_handler,
    start,
    faq,
    end_conv,
    ua_tg,
    hero_winrates,
    users_leaderboard
)

from matches_parsing import start_job

MATCH_ID = 1
REG = 2

if __name__ == '__main__':
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🔍 Search LIVE game by id$"), message_handler),
            MessageHandler(filters.Regex(r"^Registration$"), message_handler)
        ],
        states={
            MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, match_id_handler)],
            REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_handler)]
        },
        fallbacks=[
            MessageHandler(filters.Command("start") |
                           filters.Command("faq") |
                           filters.Command("ua_tg") |
                           filters.Command("hero_winrates") |
                           filters.Command("users_leaderboard"),
                           end_conv)
        ]
    )

    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(CommandHandler("ua_tg", ua_tg))
    application.add_handler(CommandHandler("hero_winrates", hero_winrates))
    application.add_handler(CommandHandler("users_leaderboard", users_leaderboard))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(CallbackQueryHandler(callback_data_handler))
    application.job_queue.run_once(start_job, when=0)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv('PORT', '8443')),
        secret_token=os.getenv('SECRET_TOKEN'),
        webhook_url=os.getenv('WEBHOOK_URL')
    )
