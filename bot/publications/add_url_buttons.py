"""
Handler pour l'ajout de boutons URL aux posts
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

from db.repositories.posts_repo import PostsRepository
from db.motor_client import get_database
from logger import setup_logger

logger = setup_logger(__name__)

# États de la conversation
WAITING_BUTTON_TEXT = 1
WAITING_BUTTON_URL = 2


async def handle_add_button_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande d'ajout de bouton URL"""
    try:
        if not context.args:
            await update.message.reply_text(
                "Usage: /add_button <code>POST_ID</code>\n\n"
                "Exemple: /add_button 123456",
                parse_mode="HTML"
            )
            return
        
        post_id = context.args[0]
        user_id = update.effective_user.id
        
        # Vérifier que le post appartient à l'utilisateur
        db = await get_database()
        posts_repo = PostsRepository(db)
        post = await posts_repo.get_post(post_id)
        
        if not post:
            await update.message.reply_text("❌ Post non trouvé")
            return
        
        if post.user_id != user_id:
            await update.message.reply_text("❌ Vous ne pouvez pas modifier ce post")
            return
        
        # Stocker le post_id dans le contexte utilisateur
        context.user_data["adding_button_post_id"] = post_id
        
        # Demander le texte du bouton
        await update.message.reply_text(
            f"🔗 <b>Ajout de bouton URL</b>\n\n"
            f"🆔 <b>Post ID:</b> <code>{post_id}</code>\n\n"
            f"<i>Envoyez le texte qui sera affiché sur le bouton:</i>\n"
            f"<i>Exemple: \"Voir plus\", \"Télécharger\", etc.</i>",
            parse_mode="HTML"
        )
        
        return WAITING_BUTTON_TEXT
        
    except Exception as e:
        logger.error(f"Erreur commande add_button: {e}")
        await update.message.reply_text("❌ Erreur lors de l'ajout du bouton")
        return ConversationHandler.END


async def handle_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la saisie du texte du bouton"""
    try:
        button_text = update.message.text.strip()
        
        if len(button_text) > 64:
            await update.message.reply_text(
                "❌ Le texte du bouton est trop long (max 64 caractères)\n"
                "Veuillez saisir un texte plus court:"
            )
            return WAITING_BUTTON_TEXT
        
        # Stocker le texte du bouton
        context.user_data["button_text"] = button_text
        
        # Demander l'URL
        await update.message.reply_text(
            f"🔗 <b>Bouton: {button_text}</b>\n\n"
            f"<i>Maintenant, envoyez l'URL du bouton:</i>\n"
            f"<i>Exemple: https://example.com</i>",
            parse_mode="HTML"
        )
        
        return WAITING_BUTTON_URL
        
    except Exception as e:
        logger.error(f"Erreur saisie texte bouton: {e}")
        await update.message.reply_text("❌ Erreur lors de la saisie")
        return ConversationHandler.END


async def handle_button_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la saisie de l'URL du bouton"""
    try:
        button_url = update.message.text.strip()
        
        # Validation basique de l'URL
        if not button_url.startswith(("http://", "https://")):
            await update.message.reply_text(
                "❌ L'URL doit commencer par http:// ou https://\n"
                "Veuillez saisir une URL valide:"
            )
            return WAITING_BUTTON_URL
        
        # Récupérer les données stockées
        post_id = context.user_data.get("adding_button_post_id")
        button_text = context.user_data.get("button_text")
        
        if not post_id or not button_text:
            await update.message.reply_text("❌ Données manquantes, recommencez avec /add_button")
            return ConversationHandler.END
        
        # Ajouter le bouton au post
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        success = await posts_repo.add_url_button(post_id, button_text, button_url)
        
        if success:
            # Rafraîchir la preview du post
            await refresh_post_preview(update, context, post_id, button_text, button_url)
            
            # Nettoyer le contexte
            context.user_data.pop("adding_button_post_id", None)
            context.user_data.pop("button_text", None)
            
            await update.message.reply_text(
                f"✅ <b>Bouton ajouté avec succès!</b>\n\n"
                f"🔗 <b>Texte:</b> {button_text}\n"
                f"🌐 <b>URL:</b> {button_url}\n"
                f"🆔 <b>Post ID:</b> <code>{post_id}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Erreur lors de l'ajout du bouton")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur saisie URL bouton: {e}")
        await update.message.reply_text("❌ Erreur lors de la saisie")
        return ConversationHandler.END


async def refresh_post_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str, button_text: str, button_url: str):
    """Rafraîchit la preview du post avec le nouveau bouton"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post mis à jour
        post = await posts_repo.get_post(post_id)
        if not post:
            return
        
        # Construire le nouveau clavier
        keyboard = build_post_keyboard_with_buttons(post)
        
        # Afficher un message de confirmation
        await update.message.reply_text(
            f"🔄 <b>Preview mise à jour</b>\n\n"
            f"<i>Le post a été mis à jour avec le nouveau bouton.</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur rafraîchissement preview: {e}")


def build_post_keyboard_with_buttons(post) -> InlineKeyboardMarkup:
    """Construit le clavier du post avec les boutons URL"""
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
    
    return InlineKeyboardMarkup(keyboard) if keyboard else None


async def handle_buttons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str):
    """Affiche le menu de gestion des boutons pour un post"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post
        post = await posts_repo.get_post(post_id)
        if not post:
            await update.callback_query.edit_message_text("❌ Post non trouvé")
            return
        
        # Construire le menu des boutons
        keyboard = build_buttons_menu_keyboard(post_id, post.inline_buttons)
        
        await update.callback_query.edit_message_text(
            f"🔗 <b>Gestion des boutons URL</b>\n\n"
            f"🆔 <b>Post ID:</b> <code>{post_id}</code>\n"
            f"🔗 <b>Boutons actuels:</b> {len(post.inline_buttons) if post.inline_buttons else 0}\n\n"
            f"<i>Sélectionnez une action:</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Erreur menu boutons: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors de l'affichage du menu")


def build_buttons_menu_keyboard(post_id: str, buttons: list) -> InlineKeyboardMarkup:
    """Construit le clavier du menu des boutons"""
    keyboard = []
    
    # Boutons d'action
    keyboard.append([
        InlineKeyboardButton("➕ Ajouter bouton", callback_data=f"add_button:{post_id}"),
        InlineKeyboardButton("✏️ Modifier bouton", callback_data=f"edit_button:{post_id}")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🗑️ Supprimer bouton", callback_data=f"delete_button:{post_id}"),
        InlineKeyboardButton("👁️ Voir tous", callback_data=f"view_buttons:{post_id}")
    ])
    
    # Bouton retour
    keyboard.append([
        InlineKeyboardButton("🔙 Retour", callback_data=f"preview:{post_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def handle_cancel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule l'ajout de bouton"""
    # Nettoyer le contexte
    context.user_data.pop("adding_button_post_id", None)
    context.user_data.pop("button_text", None)
    
    await update.message.reply_text(
        "❌ Ajout de bouton annulé",
        parse_mode="HTML"
    )
    
    return ConversationHandler.END


# Handler de conversation pour l'ajout de boutons
def get_add_button_conversation_handler():
    """Retourne le handler de conversation pour l'ajout de boutons"""
    return ConversationHandler(
        entry_points=[CommandHandler("add_button", handle_add_button_command)],
        states={
            WAITING_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_text)],
            WAITING_BUTTON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_url)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel_button)]
    )
