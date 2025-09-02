"""
Handler pour la commande /start
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from db.repositories.users_repo import UsersRepository
from models.user import User
from logger import setup_logger

logger = setup_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /start"""
    try:
        user_tg = update.effective_user
        
        # Créer/mettre à jour l'utilisateur (DESACTIVE TEMPORAIREMENT)
        # db = context.bot_data.get('db')
        # if db:
        #     users_repo = UsersRepository(db)
        #     
        #     user = User(
        #         user_id=user_tg.id,
        #         username=user_tg.username,
        #         first_name=user_tg.first_name,
        #         last_name=user_tg.last_name,
        #         language_code=user_tg.language_code
        #     )
        #     
        #     await users_repo.upsert_user(user)
        #     await users_repo.update_last_seen(user_tg.id)
        
        # Message de bienvenue
        text = (
            f"👋 Bienvenue {user_tg.first_name}!\n\n"
            "🤖 Je suis votre assistant de publication Telegram.\n\n"
            "Fonctionnalités:\n"
            "📤 Publier dans vos canaux\n"
            "⏰ Planifier des publications\n"
            "✏️ Renommer des fichiers\n"
            "🖼 Gérer les thumbnails\n\n"
            "Utilisez /help pour plus d'informations."
        )
        
        keyboard = [
            [InlineKeyboardButton("📢 Mes canaux", callback_data="menu:channels")],
            [InlineKeyboardButton("📝 Nouveau post", callback_data="menu:new_post")],
            [InlineKeyboardButton("⚙️ Paramètres", callback_data="menu:settings")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur dans start_command: {e}")
        await update.message.reply_text("❌ Une erreur s'est produite.")


def get_start_handler() -> CommandHandler:
    """Retourne le handler pour /start"""
    return CommandHandler("start", start_command)
