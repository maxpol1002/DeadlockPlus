import os

from telegram import Update

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from bot import start, message_handler, match_id_handler, faq

MATCH_ID = 1

if __name__ == '__main__':
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^Search LIVE game by id$"), message_handler)
        ],
        states={
            MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, match_id_handler)]
        },
        fallbacks=[]
    )

    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
