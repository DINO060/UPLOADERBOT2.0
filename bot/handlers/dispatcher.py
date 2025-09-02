"""
Dispatcher central pour enregistrer tous les handlers
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .start import get_start_handler
from ..logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(app: Application):
    """
    Enregistre tous les handlers de l'application
    
    Args:
        app: Application PTB
    """
    try:
        # Handlers de commandes
        app.add_handler(get_start_handler())
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("cancel", cancel_command))
        app.add_handler(CommandHandler("settings", settings_command))
        
        # Handlers de callback queries
        app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings:"))
        
        # Handlers de messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        
        logger.info("✅ Tous les handlers ont été enregistrés")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des handlers: {e}")
        raise


# Handlers simplifiés temporaires
async def help_command(update, context):
    """Commande /help"""
    await update.message.reply_text(
        "📚 <b>Aide</b>\n\n"
        "/start - Démarrer le bot\n"
        "/help - Afficher cette aide\n"
        "/settings - Paramètres\n"
        "/cancel - Annuler l'opération en cours",
        parse_mode="HTML"
    )


async def cancel_command(update, context):
    """Commande /cancel"""
    await update.message.reply_text("❌ Opération annulée")


async def settings_command(update, context):
    """Commande /settings"""
    await update.message.reply_text("⚙️ Paramètres (en construction)")


async def menu_callback(update, context):
    """Gère les callbacks du menu"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split(":")[1]
    
    if action == "channels":
        await query.edit_message_text("📢 Gestion des canaux (en construction)")
    elif action == "new_post":
        await query.edit_message_text("📝 Nouveau post (en construction)")
    elif action == "settings":
        await query.edit_message_text("⚙️ Paramètres (en construction)")


async def settings_callback(update, context):
    """Gère les callbacks des paramètres"""
    query = update.callback_query
    await query.answer("En construction")


async def handle_text(update, context):
    """Gère les messages texte"""
    await update.message.reply_text("Message reçu. Utilisez /help pour voir les commandes.")


async def handle_photo(update, context):
    """Gère les photos"""
    await update.message.reply_text("Photo reçue!")


async def handle_document(update, context):
    """Gère les documents"""
    await update.message.reply_text("Document reçu!")
