"""
Handler pour l'ajout de réactions aux posts
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db.repositories.posts_repo import PostsRepository
from db.motor_client import get_database
from logger import setup_logger

logger = setup_logger(__name__)


async def handle_reaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les callbacks de réactions (react:emoji:post_id)"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Extraire les données
        data_parts = query.data.split(":")
        if len(data_parts) != 3:
            await query.edit_message_text("❌ Format de callback invalide")
            return
        
        action, emoji, post_id = data_parts
        
        if action != "react":
            await query.edit_message_text("❌ Action non reconnue")
            return
        
        # Traiter la réaction
        await process_reaction(update, context, post_id, emoji)
        
    except Exception as e:
        logger.error(f"Erreur callback réaction: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors du traitement de la réaction")


async def process_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str, emoji: str):
    """Traite l'ajout d'une réaction"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post
        post = await posts_repo.get_post(post_id)
        if not post:
            await update.callback_query.edit_message_text("❌ Post non trouvé")
            return
        
        # Ajouter la réaction en DB
        success = await posts_repo.add_reaction(post_id, emoji)
        if not success:
            await update.callback_query.edit_message_text("❌ Erreur lors de l'ajout de la réaction")
            return
        
        # Incrémenter le compteur de réactions
        await posts_repo.inc_reaction(post_id, 1)
        
        # Rafraîchir le clavier avec la nouvelle réaction
        await refresh_reaction_keyboard(update, context, post_id, emoji)
        
    except Exception as e:
        logger.error(f"Erreur traitement réaction: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors du traitement")


async def refresh_reaction_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str, new_emoji: str):
    """Rafraîchit le clavier avec la nouvelle réaction"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post mis à jour
        post = await posts_repo.get_post(post_id)
        if not post:
            return
        
        # Construire le nouveau clavier
        keyboard = build_reaction_keyboard(post)
        
        # Mettre à jour le message
        if post.content_type == "text":
            await update.callback_query.edit_message_text(
                post.text or "[Pas de texte]",
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=post.disable_web_page_preview
            )
        else:
            # Pour les médias, on ne peut éditer que la légende
            caption = post.caption or f"📎 Type: {post.content_type}"
            await update.callback_query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        # Afficher une confirmation temporaire
        await update.callback_query.answer(f"👍 Réaction {new_emoji} ajoutée!")
        
    except Exception as e:
        logger.error(f"Erreur rafraîchissement clavier: {e}")


def build_reaction_keyboard(post) -> InlineKeyboardMarkup:
    """Construit le clavier avec les réactions"""
    keyboard = []
    
    # Ajouter les boutons URL existants
    if post.inline_buttons:
        for row in post.inline_buttons:
            keyboard.append(row)
    
    # Ajouter les réactions populaires
    if post.reactions:
        reaction_row = []
        for reaction in post.reactions[:8]:  # Limiter à 8 réactions
            reaction_row.append(
                InlineKeyboardButton(
                    reaction,
                    callback_data=f"react:{reaction}:{post._id}"
                )
            )
        if reaction_row:
            keyboard.append(reaction_row)
    
    # Ajouter un bouton pour ajouter de nouvelles réactions
    keyboard.append([
        InlineKeyboardButton(
            "➕ Ajouter réaction",
            callback_data=f"add_reaction:{post._id}"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard) if keyboard else None


async def handle_add_reaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande d'ajout de réaction"""
    try:
        if not context.args:
            await update.message.reply_text(
                "Usage: /add_reaction <code>POST_ID</code> <code>EMOJI</code>\n\n"
                "Exemple: /add_reaction 123456 👍",
                parse_mode="HTML"
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ ID du post et emoji requis")
            return
        
        post_id = context.args[0]
        emoji = context.args[1]
        
        # Traiter la réaction
        await process_reaction(update, context, post_id, emoji)
        
        await update.message.reply_text(
            f"✅ Réaction {emoji} ajoutée au post {post_id}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur commande add_reaction: {e}")
        await update.message.reply_text("❌ Erreur lors de l'ajout de la réaction")


async def show_reactions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str):
    """Affiche le menu des réactions pour un post"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post
        post = await posts_repo.get_post(post_id)
        if not post:
            await update.callback_query.edit_message_text("❌ Post non trouvé")
            return
        
        # Construire le menu des réactions
        keyboard = build_reactions_menu_keyboard(post_id, post.reactions)
        
        await update.callback_query.edit_message_text(
            f"👍 <b>Gestion des réactions</b>\n\n"
            f"🆔 <b>Post ID:</b> <code>{post_id}</code>\n"
            f"📊 <b>Réactions actuelles:</b> {len(post.reactions)}\n"
            f"🔢 <b>Total clics:</b> {post.reactions_count}\n\n"
            f"<i>Sélectionnez une action:</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Erreur menu réactions: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors de l'affichage du menu")


def build_reactions_menu_keyboard(post_id: str, reactions: list) -> InlineKeyboardMarkup:
    """Construit le clavier du menu des réactions"""
    keyboard = []
    
    # Réactions populaires
    popular_reactions = ["👍", "❤️", "🔥", "👏", "🎉", "💯", "🚀", "⭐"]
    
    # Première ligne: réactions populaires
    popular_row = []
    for emoji in popular_reactions[:4]:
        popular_row.append(
            InlineKeyboardButton(
                emoji,
                callback_data=f"react:{emoji}:{post_id}"
            )
        )
    keyboard.append(popular_row)
    
    # Deuxième ligne: réactions populaires restantes
    popular_row2 = []
    for emoji in popular_reactions[4:8]:
        popular_row2.append(
            InlineKeyboardButton(
                emoji,
                callback_data=f"react:{emoji}:{post_id}"
            )
        )
    keyboard.append(popular_row2)
    
    # Troisième ligne: réactions existantes
    if reactions:
        existing_row = []
        for reaction in reactions[:6]:  # Limiter à 6
            existing_row.append(
                InlineKeyboardButton(
                    reaction,
                    callback_data=f"react:{reaction}:{post_id}"
                )
            )
        if existing_row:
            keyboard.append(existing_row)
    
    # Boutons d'action
    keyboard.append([
        InlineKeyboardButton("➕ Ajouter personnalisé", callback_data=f"custom_reaction:{post_id}"),
        InlineKeyboardButton("🔙 Retour", callback_data=f"preview:{post_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)
