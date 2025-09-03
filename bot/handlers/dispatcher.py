"""
Dispatcher central pour enregistrer tous les handlers
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .start import get_start_handler
from . import cancel, channels
from ..logger import setup_logger

# Import des handlers de publications
from ..publications import receive_post, preview_post, send_post, add_reactions, add_url_buttons

logger = setup_logger(__name__)


def register_handlers(app: Application):
    """
    Enregistre tous les handlers de l'application
    
    Args:
        app: Application PTB
    """
    try:
        # ============ Handlers de commandes ============
        app.add_handler(get_start_handler())
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("cancel", cancel.handle_cancel_command))
        app.add_handler(CommandHandler("settings", settings_command))
        
        # Commandes pour les posts
        app.add_handler(CommandHandler("drafts", show_drafts))
        app.add_handler(CommandHandler("send", send_post_command))
        app.add_handler(CommandHandler("delete", delete_post))
        app.add_handler(CommandHandler("channels", channels.handle_channels_command))
        app.add_handler(CommandHandler("preview", preview_post.handle_preview_command))
        
        # Commandes pour les réactions et boutons
        app.add_handler(CommandHandler("add_reaction", add_reactions.handle_add_reaction_command))
        app.add_handler(add_url_buttons.get_add_button_conversation_handler())
        
        # ============ Handlers de callback queries ============
        app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
        # Annulations via callback générique
        app.add_handler(CallbackQueryHandler(cancel.handle_cancel_callback, pattern="^cancel$"))
        app.add_handler(CallbackQueryHandler(cancel.handle_cancel_send, pattern="^cancel_send$"))
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings:"))
        app.add_handler(CallbackQueryHandler(draft_callback, pattern="^draft:"))
        # Canaux
        app.add_handler(channels.get_channels_conversation_handler())
        app.add_handler(CallbackQueryHandler(channels.handle_manage_channel, pattern="^manage_channel:"))
        app.add_handler(CallbackQueryHandler(channels.handle_toggle_channel, pattern="^toggle_channel:"))
        app.add_handler(CallbackQueryHandler(channels.handle_delete_channel, pattern="^delete_channel:"))
        app.add_handler(CallbackQueryHandler(channels.handle_confirm_delete_channel, pattern="^confirm_delete_channel:"))
        app.add_handler(CallbackQueryHandler(channels.handle_refresh_channels, pattern="^refresh_channels$"))
        app.add_handler(CallbackQueryHandler(channels.handle_channel_help, pattern="^channel_help$"))
        
        # ============ Handlers de publications (PRIORITÉ 3) ============
        # Envoi de posts
        app.add_handler(CallbackQueryHandler(send_post.send_to_selected_channels, pattern="^confirm_send:"))
        app.add_handler(CallbackQueryHandler(send_post.handle_send_post, pattern="^send:"))
        app.add_handler(CallbackQueryHandler(send_post.toggle_channel_selection, pattern="^select_channel:"))
        app.add_handler(CallbackQueryHandler(send_post.cancel_send_callback, pattern="^cancel_send:"))
        
        # Réactions (pattern: react:emoji:post_id)
        app.add_handler(CallbackQueryHandler(add_reactions.handle_reaction_callback, pattern="^react:"))
        app.add_handler(CallbackQueryHandler(add_reactions.show_reactions_menu, pattern="^reactions:"))
        
        # Boutons URL
        app.add_handler(CallbackQueryHandler(add_url_buttons.handle_buttons_menu, pattern="^buttons:"))
        
        # ============ Handlers de réception de posts (PRIORITÉ 2) ============
        # IMPORTANT: Les media_group doivent être traités en premier
        app.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO,
            receive_post.handle_media_group
        ))
        
        # Handlers pour chaque type de média
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_post.handle_text_message
        ))
        
        app.add_handler(MessageHandler(
            filters.PHOTO,
            receive_post.handle_photo_message
        ))
        
        app.add_handler(MessageHandler(
            filters.VIDEO,
            receive_post.handle_video_message
        ))
        
        app.add_handler(MessageHandler(
            filters.Document.ALL,
            receive_post.handle_document_message
        ))
        
        app.add_handler(MessageHandler(
            filters.AUDIO,
            receive_post.handle_audio_message
        ))
        
        app.add_handler(MessageHandler(
            filters.ANIMATION,
            receive_post.handle_animation_message
        ))
        
        app.add_handler(MessageHandler(
            filters.VOICE,
            receive_post.handle_voice_message
        ))
        
        app.add_handler(MessageHandler(
            filters.VIDEO_NOTE,
            receive_post.handle_video_note_message
        ))
        
        logger.info("✅ Tous les handlers ont été enregistrés")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des handlers: {e}")
        raise


# ============ Handlers de commandes ============

async def help_command(update, context):
    """Commande /help"""
    await update.message.reply_text(
        "📚 <b>Aide du Bot Uploader</b>\n\n"
        "<b>📝 Création de posts:</b>\n"
        "• Envoyez du texte, photo, vidéo, document, etc.\n"
        "• Le bot créera automatiquement un draft\n\n"
        "<b>📤 Gestion des posts:</b>\n"
        "/drafts - Voir vos drafts\n"
        "/preview - Prévisualiser le dernier draft\n"
        "/send <code>ID</code> - Envoyer un post\n"
        "/delete <code>ID</code> - Supprimer un post\n\n"
        "<b>👍 Réactions et boutons:</b>\n"
        "/add_reaction <code>ID</code> <code>EMOJI</code> - Ajouter une réaction\n"
        "/add_button <code>ID</code> - Ajouter un bouton URL\n\n"
        "<b>📢 Gestion des canaux:</b>\n"
        "/channels - Gérer vos canaux\n\n"
        "<b>⚙️ Autres commandes:</b>\n"
        "/settings - Paramètres\n"
        "/cancel - Annuler l'opération en cours\n"
        "/start - Menu principal",
        parse_mode="HTML"
    )


async def cancel_command(update, context):
    """Commande /cancel"""
    # Nettoyer le contexte utilisateur si nécessaire
    context.user_data.clear()
    await update.message.reply_text("❌ Opération annulée")


async def settings_command(update, context):
    """Commande /settings"""
    await update.message.reply_text(
        "⚙️ <b>Paramètres</b>\n\n"
        "• Timezone: UTC\n"
        "• Auto-delete: 24h\n"
        "• Reactions: ✅\n"
        "• Boutons URL: ✅\n\n"
        "<i>Paramètres avancés en construction...</i>",
        parse_mode="HTML"
    )


async def show_drafts(update, context):
    """Affiche les drafts de l'utilisateur"""
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        user_id = update.message.from_user.id
        
        # Récupérer les drafts depuis la DB
        try:
            db = await get_database()
            posts_repo = PostsRepository(db)
            drafts = await posts_repo.get_draft_posts(user_id)
            
            if not drafts:
                await update.message.reply_text(
                    "📭 Vous n'avez aucun draft.\n\n"
                    "Envoyez du contenu pour créer un draft!",
                    parse_mode="HTML"
                )
                return
            
            # Afficher la liste des drafts
            text = "📝 <b>Vos drafts:</b>\n\n"
            for draft in drafts[:10]:  # Limiter à 10
                preview = ""
                if draft.text:
                    preview = draft.text[:30] + ("..." if len(draft.text) > 30 else "")
                elif draft.caption:
                    preview = draft.caption[:30] + ("..." if len(draft.caption) > 30 else "")
                else:
                    preview = f"[{draft.content_type}]"
                
                text += f"• <code>{draft._id}</code> - {preview}\n"
            
            if len(drafts) > 10:
                text += f"\n<i>...et {len(drafts) - 10} autres drafts</i>"
            
            await update.message.reply_text(text, parse_mode="HTML")
            
        except Exception as db_error:
            await update.message.reply_text(
                "⚠️ Base de données non disponible (mode test)",
                parse_mode="HTML"
            )
    
    except Exception as e:
        logger.error(f"Erreur dans show_drafts: {e}")
        await update.message.reply_text("❌ Erreur lors de la récupération des drafts")


async def send_post_command(update, context):
    """Commande /send pour envoyer un post"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /send <code>POST_ID</code>",
            parse_mode="HTML"
        )
        return
    
    post_id = context.args[0]
    await send_post.handle_send_post(update, context, post_id)


async def delete_post(update, context):
    """Supprime un post (placeholder)"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /delete <code>POST_ID</code>",
            parse_mode="HTML"
        )
        return
    
    post_id = context.args[0]
    await update.message.reply_text(
        f"🗑️ Suppression du post <code>{post_id}</code> (en construction...)",
        parse_mode="HTML"
    )


async def manage_channels(update, context):
    """Gère les canaux (placeholder)"""
    await update.message.reply_text(
        "📢 <b>Gestion des canaux</b>\n\n"
        "<i>Cette fonctionnalité sera bientôt disponible...</i>",
        parse_mode="HTML"
    )


# ============ Handlers de callbacks ============

async def menu_callback(update, context):
    """Gère les callbacks du menu"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split(":")[1]
    
    if action == "channels":
        await query.edit_message_text("📢 Gestion des canaux (en construction)")
    elif action == "new_post":
        await query.edit_message_text(
            "📝 Pour créer un nouveau post, envoyez simplement:\n"
            "• Du texte\n"
            "• Une photo\n"
            "• Une vidéo\n"
            "• Un document\n"
            "• Etc.",
            parse_mode="HTML"
        )
    elif action == "drafts":
        # Trigger show_drafts
        await show_drafts(query, context)
    elif action == "preview":
        await query.edit_message_text(
            "📝 Utilisez /preview pour prévisualiser votre dernier draft",
            parse_mode="HTML"
        )
    elif action == "settings":
        await query.edit_message_text("⚙️ Paramètres (en construction)")


async def settings_callback(update, context):
    """Gère les callbacks des paramètres"""
    query = update.callback_query
    await query.answer("En construction")


async def draft_callback(update, context):
    """Gère les callbacks des drafts"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(":")
    if len(data_parts) < 2:
        return
    
    action = data_parts[1]
    post_id = data_parts[2] if len(data_parts) > 2 else None
    
    if action == "send" and post_id:
        await send_post.handle_send_post(update, context, post_id)
    elif action == "edit" and post_id:
        await query.edit_message_text(
            f"✏️ Édition du post {post_id} (en construction...)",
            parse_mode="HTML"
        )
    elif action == "delete" and post_id:
        await query.edit_message_text(
            f"🗑️ Suppression du post {post_id} (en construction...)",
            parse_mode="HTML"
        )
    elif action == "preview" and post_id:
        await preview_post.handle_preview_command(update, context)


# Placeholder supprimé: la gestion des canaux est couverte par bot/handlers/channels.py