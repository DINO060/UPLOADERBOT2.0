"""
Gestionnaire pour l'ajout et la gestion des canaux
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from ..db.repositories.channels_repo import ChannelsRepository
from ..db.repositories.users_repo import UsersRepository
from ..db.motor_client import get_database
from ..models.channel import Channel
from ..logger import setup_logger

logger = setup_logger(__name__)

# États de conversation
WAITING_CHANNEL_ID = 1
WAITING_CHANNEL_CONFIRM = 2


async def handle_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /channels"""
    try:
        user_id = update.effective_user.id
        
        # Récupérer les canaux de l'utilisateur
        db = await get_database()
        channels_repo = ChannelsRepository(db)
        channels = await channels_repo.get_user_channels(user_id)
        
        if not channels:
            # Aucun canal, proposer d'en ajouter
            keyboard = [[
                InlineKeyboardButton("➕ Ajouter un canal", callback_data="add_channel"),
                InlineKeyboardButton("❓ Aide", callback_data="channel_help")
            ]]
            
            await update.message.reply_text(
                "📢 <b>Gestion des canaux</b>\n\n"
                "Vous n'avez pas encore de canaux configurés.\n"
                "Ajoutez un canal pour commencer à publier!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Afficher la liste des canaux
            text = "📢 <b>Vos canaux:</b>\n\n"
            keyboard = []
            
            for channel in channels[:10]:  # Limiter à 10 pour l'affichage
                status = "✅" if channel.is_active else "❌"
                text += f"{status} {channel.display_name}\n"
                
                # Bouton pour chaque canal
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status} {channel.display_name}",
                        callback_data=f"manage_channel:{channel.channel_id}"
                    )
                ])
            
            # Boutons d'action
            keyboard.append([
                InlineKeyboardButton("➕ Ajouter", callback_data="add_channel"),
                InlineKeyboardButton("🔄 Rafraîchir", callback_data="refresh_channels")
            ])
            
            await update.message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
    except Exception as e:
        logger.error(f"Erreur channels: {e}")
        await update.message.reply_text("❌ Erreur lors de la récupération des canaux")


async def handle_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre le processus d'ajout d'un canal"""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_text(
            "📢 <b>Ajouter un canal</b>\n\n"
            "Pour ajouter un canal, le bot doit être administrateur dans ce canal.\n\n"
            "<b>Étapes:</b>\n"
            "1. Ajoutez le bot comme admin dans votre canal\n"
            "2. Donnez-lui les permissions pour poster\n"
            "3. Envoyez-moi l'ID ou @username du canal\n\n"
            "<i>Exemple: @monchannel ou -1001234567890</i>\n\n"
            "Envoyez /cancel pour annuler.",
            parse_mode="HTML"
        )
        
        # Passer en mode attente de l'ID
        return WAITING_CHANNEL_ID
        
    except Exception as e:
        logger.error(f"Erreur add channel: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_channel_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traite l'ID du canal fourni par l'utilisateur"""
    try:
        user_id = update.effective_user.id
        channel_input = update.message.text.strip()
        
        # Vérifier le format
        if not channel_input.startswith("@") and not channel_input.startswith("-100"):
            await update.message.reply_text(
                "❌ Format invalide!\n\n"
                "Utilisez @username ou l'ID numérique (-100...)",
                parse_mode="HTML"
            )
            return WAITING_CHANNEL_ID
        
        # Tenter de récupérer les infos du canal
        try:
            chat = await context.bot.get_chat(channel_input)
            
            # Vérifier que c'est bien un canal
            if chat.type not in ["channel", "supergroup"]:
                await update.message.reply_text(
                    "❌ Ce n'est pas un canal valide!",
                    parse_mode="HTML"
                )
                return WAITING_CHANNEL_ID
            
            # Vérifier que le bot est admin
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if bot_member.status not in ["administrator", "creator"]:
                await update.message.reply_text(
                    "❌ Le bot n'est pas administrateur dans ce canal!\n\n"
                    "Ajoutez d'abord le bot comme admin.",
                    parse_mode="HTML"
                )
                return WAITING_CHANNEL_ID
            
            # Vérifier les permissions
            if hasattr(bot_member, "can_post_messages") and not bot_member.can_post_messages:
                await update.message.reply_text(
                    "❌ Le bot n'a pas la permission de poster!\n\n"
                    "Donnez-lui la permission 'Poster des messages'.",
                    parse_mode="HTML"
                )
                return WAITING_CHANNEL_ID
            
            # Créer l'objet Channel
            member_count = 0
            try:
                member_count = await context.bot.get_chat_member_count(chat.id)
            except Exception:
                pass
            
            channel = Channel(
                channel_id=chat.id,
                user_id=user_id,
                username=chat.username,
                title=chat.title,
                description=getattr(chat, "description", None),
                member_count=member_count,
                is_broadcast=chat.type == "channel",
                can_post_messages=getattr(bot_member, "can_post_messages", True),
                can_edit_messages=getattr(bot_member, "can_edit_messages", True),
                can_delete_messages=getattr(bot_member, "can_delete_messages", True)
            )
            
            # Stocker temporairement
            context.user_data['pending_channel'] = channel
            
            # Demander confirmation
            keyboard = [[
                InlineKeyboardButton("✅ Confirmer", callback_data="confirm_add_channel"),
                InlineKeyboardButton("❌ Annuler", callback_data="cancel_add_channel")
            ]]
            
            info_text = (
                f"📢 <b>Canal trouvé!</b>\n\n"
                f"<b>Nom:</b> {chat.title}\n"
                f"<b>Type:</b> {'Canal' if chat.type == 'channel' else 'Supergroupe'}\n"
                f"<b>Membres:</b> {channel.member_count}\n"
                f"<b>Username:</b> @{chat.username if chat.username else 'Privé'}\n\n"
                f"Voulez-vous ajouter ce canal?"
            )
            
            await update.message.reply_text(
                info_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return WAITING_CHANNEL_CONFIRM
            
        except Exception as e:
            logger.error(f"Erreur get_chat: {e}")
            await update.message.reply_text(
                "❌ Impossible d'accéder à ce canal.\n\n"
                "Vérifiez que:\n"
                "• L'ID est correct\n"
                "• Le bot est membre du canal\n"
                "• Le bot a les permissions nécessaires",
                parse_mode="HTML"
            )
            return WAITING_CHANNEL_ID
        
    except Exception as e:
        logger.error(f"Erreur channel input: {e}")
        await update.message.reply_text("❌ Erreur lors du traitement")
        return ConversationHandler.END


async def handle_confirm_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirme l'ajout du canal"""
    query = update.callback_query
    await query.answer()
    
    try:
        channel = context.user_data.get('pending_channel')
        if not channel:
            await query.edit_message_text("❌ Aucun canal en attente")
            return ConversationHandler.END
        
        # Sauvegarder en DB
        db = await get_database()
        channels_repo = ChannelsRepository(db)
        
        # Vérifier si le canal existe déjà
        existing = await channels_repo.get_channel(channel.channel_id)
        if existing and existing.user_id == channel.user_id:
            await query.edit_message_text(
                "⚠️ Ce canal est déjà dans votre liste!",
                parse_mode="HTML"
            )
        else:
            # Ajouter le canal
            success = await channels_repo.upsert_channel(channel)
            
            if success:
                await query.edit_message_text(
                    f"✅ <b>Canal ajouté avec succès!</b>\n\n"
                    f"📢 {channel.title}\n\n"
                    f"Vous pouvez maintenant publier dans ce canal.",
                    parse_mode="HTML"
                )
                
                # Mettre à jour les stats utilisateur
                users_repo = UsersRepository(db)
                await users_repo.update_user(
                    channel.user_id,
                    {"$inc": {"total_channels": 1}}
                )
            else:
                await query.edit_message_text("❌ Erreur lors de l'ajout")
        
        # Nettoyer le contexte
        context.user_data.pop('pending_channel', None)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur confirm add: {e}")
        await query.edit_message_text("❌ Erreur")
        return ConversationHandler.END


async def handle_manage_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère un canal spécifique"""
    query = update.callback_query
    await query.answer()
    
    try:
        channel_id = int(query.data.split(":")[1])
        user_id = update.effective_user.id
        
        # Récupérer le canal
        db = await get_database()
        channels_repo = ChannelsRepository(db)
        channel = await channels_repo.get_channel(channel_id)
        
        if not channel or channel.user_id != user_id:
            await query.edit_message_text("❌ Canal introuvable")
            return
        
        # Afficher les options
        status = "✅ Actif" if channel.is_active else "❌ Inactif"
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'🔴 Désactiver' if channel.is_active else '🟢 Activer'}",
                callback_data=f"toggle_channel:{channel_id}"
            )],
            [InlineKeyboardButton(
                "📊 Statistiques",
                callback_data=f"channel_stats:{channel_id}"
            )],
            [InlineKeyboardButton(
                "🗑️ Supprimer",
                callback_data=f"delete_channel:{channel_id}"
            )],
            [InlineKeyboardButton(
                "🔙 Retour",
                callback_data="back_to_channels"
            )]
        ]
        
        info_text = (
            f"📢 <b>{channel.title}</b>\n\n"
            f"<b>Status:</b> {status}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n"
            f"<b>Membres:</b> {channel.member_count}\n"
            f"<b>Posts envoyés:</b> {channel.total_posts}\n"
        )
        
        if channel.username:
            info_text += f"<b>Lien:</b> @{channel.username}\n"
        
        await query.edit_message_text(
            info_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Erreur manage channel: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_toggle_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Active/désactive un canal"""
    query = update.callback_query
    await query.answer()
    
    try:
        channel_id = int(query.data.split(":")[1])
        user_id = update.effective_user.id
        
        # Toggle le statut
        db = await get_database()
        channels_repo = ChannelsRepository(db)
        new_status = await channels_repo.toggle_channel_status(channel_id, user_id)
        
        if new_status is not None:
            status_text = "activé" if new_status else "désactivé"
            await query.answer(f"Canal {status_text}!", show_alert=True)
            
            # Rafraîchir l'affichage
            await handle_manage_channel(update, context)
        else:
            await query.answer("❌ Erreur", show_alert=True)
        
    except Exception as e:
        logger.error(f"Erreur toggle: {e}")
        await query.answer("❌ Erreur", show_alert=True)


async def handle_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Supprime un canal"""
    query = update.callback_query
    await query.answer()
    
    try:
        channel_id = int(query.data.split(":")[1])
        
        # Demander confirmation
        keyboard = [[
            InlineKeyboardButton(
                "⚠️ Confirmer la suppression",
                callback_data=f"confirm_delete_channel:{channel_id}"
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"manage_channel:{channel_id}"
            )
        ]]
        
        await query.edit_message_text(
            "⚠️ <b>Confirmation requise</b>\n\n"
            "Voulez-vous vraiment supprimer ce canal?\n"
            "Cette action est irréversible!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Erreur delete channel: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_confirm_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirme la suppression du canal"""
    query = update.callback_query
    await query.answer()
    
    try:
        channel_id = int(query.data.split(":")[1])
        user_id = update.effective_user.id
        
        db = await get_database()
        channels_repo = ChannelsRepository(db)
        success = await channels_repo.delete_channel(channel_id, user_id)
        
        if success:
            await query.edit_message_text("✅ Canal supprimé")
        else:
            await query.edit_message_text("❌ Échec de la suppression")
        
    except Exception as e:
        logger.error(f"Erreur confirm delete: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_refresh_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rafraîchit la liste des canaux"""
    query = update.callback_query
    await query.answer()
    # Réutiliser la commande
    class Dummy:
        message = None
    dummy = Dummy()
    dummy.message = query
    await handle_channels_command(dummy, context)


async def handle_channel_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'aide pour les canaux"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ <b>Aide - Canaux</b>\n\n"
        "• Ajoutez le bot comme administrateur du canal\n"
        "• Donnez-lui la permission de publier des messages\n"
        "• Utilisez /channels puis 'Ajouter un canal'\n\n"
        "Vous pourrez ensuite envoyer vos posts dans ce canal.",
        parse_mode="HTML"
    )


def get_channels_conversation_handler():
    """Conversation pour l'ajout guidé d'un canal"""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_channel, pattern="^add_channel$")],
        states={
            WAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_id_input)],
            WAITING_CHANNEL_CONFIRM: [CallbackQueryHandler(handle_confirm_add_channel, pattern="^confirm_add_channel$")],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )


