"""
Handler pour la prévisualisation des posts
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db.repositories.posts_repo import PostsRepository
from db.motor_client import get_database
from logger import setup_logger

logger = setup_logger(__name__)


async def handle_preview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande de prévisualisation"""
    try:
        user_id = update.effective_user.id
        
        # Récupérer le dernier draft
        db = await get_database()
        posts_repo = PostsRepository(db)
        drafts = await posts_repo.get_draft_posts(user_id)
        
        if not drafts:
            await update.message.reply_text(
                "📭 Aucun draft à prévisualiser.\n"
                "Envoyez du contenu pour créer un draft!",
                parse_mode="HTML"
            )
            return
        
        # Prendre le dernier draft
        post = drafts[0]
        
        # Construire la preview
        preview_text = build_preview_text(post)
        keyboard = build_preview_keyboard(post._id)
        
        # Envoyer selon le type
        if post.content_type == "text":
            await update.message.reply_text(
                preview_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=post.disable_web_page_preview
            )
        elif post.content_type == "photo" and post.file_id:
            await update.message.reply_photo(
                photo=post.file_id,
                caption=preview_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        elif post.content_type == "video" and post.file_id:
            await update.message.reply_video(
                video=post.file_id,
                caption=preview_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        elif post.content_type == "document" and post.file_id:
            await update.message.reply_document(
                document=post.file_id,
                caption=preview_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                preview_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
    except Exception as e:
        logger.error(f"Erreur preview: {e}")
        await update.message.reply_text("❌ Erreur lors de la prévisualisation")


def build_preview_text(post) -> str:
    """Construit le texte de preview"""
    if post.content_type == "text":
        return post.text or "[Pas de texte]"
    else:
        caption = post.caption or ""
        return f"📎 <b>Type:</b> {post.content_type}\n\n{caption}"


def build_preview_keyboard(post_id: str) -> InlineKeyboardMarkup:
    """Construit le clavier de preview"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Envoyer", callback_data=f"send:{post_id}"),
            InlineKeyboardButton("✏️ Modifier", callback_data=f"edit:{post_id}")
        ],
        [
            InlineKeyboardButton("👍 Réactions", callback_data=f"reactions:{post_id}"),
            InlineKeyboardButton("🔗 Boutons", callback_data=f"buttons:{post_id}")
        ],
        [
            InlineKeyboardButton("⏰ Planifier", callback_data=f"schedule:{post_id}"),
            InlineKeyboardButton("🗑️ Supprimer", callback_data=f"delete:{post_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


