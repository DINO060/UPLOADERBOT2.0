"""
Handler pour l'envoi de posts vers les canaux
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, List

from db.repositories.posts_repo import PostsRepository
from db.repositories.channels_repo import ChannelsRepository
from db.motor_client import get_database
from logger import setup_logger

logger = setup_logger(__name__)


async def handle_send_post(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str = None):
    """Gère l'envoi d'un post vers les canaux"""
    try:
        user_id = update.effective_user.id
        
        # Récupérer le post
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        if not post_id:
            # Si appelé depuis callback, extraire l'ID
            if update.callback_query:
                post_id = update.callback_query.data.split(":")[1]
            else:
                await update.message.reply_text("❌ ID du post manquant")
                return
        
        post = await posts_repo.get_post(post_id)
        if not post:
            await update.message.reply_text("❌ Post non trouvé")
            return
        
        if post.user_id != user_id:
            await update.message.reply_text("❌ Vous ne pouvez pas envoyer ce post")
            return
        
        # Récupérer les canaux de l'utilisateur
        channels_repo = ChannelsRepository(db)
        user_channels = await channels_repo.get_user_channels(user_id)
        
        if not user_channels:
            await update.message.reply_text(
                "❌ Aucun canal configuré.\n"
                "Utilisez /channels pour ajouter des canaux!",
                parse_mode="HTML"
            )
            return
        
        # Afficher la sélection des canaux
        keyboard = build_channel_selection_keyboard(post_id, user_channels)
        
        await update.message.reply_text(
            f"📤 <b>Envoi du post</b>\n\n"
            f"🆔 <b>ID:</b> <code>{post_id}</code>\n"
            f"📄 <b>Type:</b> {post.content_type}\n"
            f"📢 <b>Canaux disponibles:</b> {len(user_channels)}\n\n"
            f"<i>Sélectionnez les canaux de destination:</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Erreur envoi post: {e}")
        await update.message.reply_text("❌ Erreur lors de l'envoi")


async def toggle_channel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la sélection/désélection d'un canal et propose la confirmation"""
    try:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split(":")
        # Expected: select_channel:POST_ID:CHANNEL_ID
        if len(data_parts) < 3:
            await query.answer("❌ Données invalides", show_alert=True)
            return

        post_id = data_parts[1]
        try:
            channel_id = int(data_parts[2])
        except ValueError:
            await query.answer("❌ Canal invalide", show_alert=True)
            return

        # Stockage par post pour éviter collisions
        selection_key = f"selected_channels:{post_id}"
        selected_channels: List[int] = context.user_data.get(selection_key, [])

        if channel_id in selected_channels:
            selected_channels.remove(channel_id)
            await query.answer("Canal retiré de la sélection")
        else:
            selected_channels.append(channel_id)
            await query.answer("Canal ajouté à la sélection")

        context.user_data[selection_key] = selected_channels

        # Construire UI de confirmation si au moins un canal
        if selected_channels:
            channels_csv = ",".join(str(cid) for cid in selected_channels)
            confirm_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📤 Envoyer maintenant",
                        callback_data=f"confirm_send:{post_id}:{channels_csv}"
                    ),
                    InlineKeyboardButton(
                        "❌ Annuler",
                        callback_data=f"cancel_send:{post_id}"
                    )
                ]
            ])

            await query.edit_message_text(
                text=(
                    f"📢 <b>Canaux sélectionnés: {len(selected_channels)}</b>\n\n"
                    f"Cliquez sur 'Envoyer maintenant' pour publier."
                ),
                parse_mode="HTML",
                reply_markup=confirm_keyboard
            )
        else:
            # Si plus de sélection, ne change pas le message (l'utilisateur peut re-sélectionner)
            pass

    except Exception as e:
        logger.error(f"Erreur sélection canal: {e}")
        await update.callback_query.answer("❌ Erreur", show_alert=True)


async def cancel_send_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule un processus d'envoi en cours"""
    try:
        query = update.callback_query
        await query.answer()

        # Effacer toute sélection stockée pour ce post si présent
        data_parts = query.data.split(":")
        post_id = data_parts[1] if len(data_parts) > 1 else None
        if post_id:
            selection_key = f"selected_channels:{post_id}"
            context.user_data.pop(selection_key, None)

        await query.edit_message_text(
            "❌ <b>Envoi annulé</b>\n\nLe post n'a pas été envoyé.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Erreur cancel_send: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors de l'annulation")

async def send_to_selected_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envoie le post vers les canaux sélectionnés"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Extraire les données
        data_parts = query.data.split(":")
        action = data_parts[1]
        post_id = data_parts[2]
        channel_ids = data_parts[3].split(",") if len(data_parts) > 3 else []
        
        if action == "confirm_send":
            # Envoyer vers tous les canaux sélectionnés
            await send_post_to_channels(update, context, post_id, channel_ids)
        else:
            await query.edit_message_text("❌ Action non reconnue")
            
    except Exception as e:
        logger.error(f"Erreur envoi vers canaux: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors de l'envoi")


async def send_post_to_channels(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str, channel_ids: List[str]):
    """Envoie effectivement le post vers les canaux"""
    try:
        db = await get_database()
        posts_repo = PostsRepository(db)
        channels_repo = ChannelsRepository(db)
        
        # Récupérer le post
        post = await posts_repo.get_post(post_id)
        if not post:
            await update.callback_query.edit_message_text("❌ Post non trouvé")
            return
        
        # Récupérer les canaux
        channels = []
        for channel_id in channel_ids:
            channel = await channels_repo.get_channel(channel_id)
            if channel:
                channels.append(channel)
        
        if not channels:
            await update.callback_query.edit_message_text("❌ Aucun canal valide")
            return
        
        # Préparer le message
        message_text = post.text or post.caption or ""
        parse_mode = post.parse_mode or "HTML"
        disable_web_page_preview = post.disable_web_page_preview
        
        # Construire le clavier avec réactions et boutons
        inline_keyboard = build_post_keyboard(post)
        
        # Envoyer vers chaque canal
        sent_messages = {}
        failed_channels = []
        
        for channel in channels:
            try:
                if post.content_type == "text":
                    message = await context.bot.send_message(
                        chat_id=channel.channel_id,
                        text=message_text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                        reply_markup=inline_keyboard
                    )
                elif post.content_type == "photo" and post.file_id:
                    message = await context.bot.send_photo(
                        chat_id=channel.channel_id,
                        photo=post.file_id,
                        caption=message_text,
                        parse_mode=parse_mode,
                        reply_markup=inline_keyboard
                    )
                elif post.content_type == "video" and post.file_id:
                    message = await context.bot.send_video(
                        chat_id=channel.channel_id,
                        video=post.file_id,
                        caption=message_text,
                        parse_mode=parse_mode,
                        reply_markup=inline_keyboard
                    )
                elif post.content_type == "document" and post.file_id:
                    message = await context.bot.send_document(
                        chat_id=channel.channel_id,
                        document=post.file_id,
                        caption=message_text,
                        parse_mode=parse_mode,
                        reply_markup=inline_keyboard
                    )
                else:
                    message = await context.bot.send_message(
                        chat_id=channel.channel_id,
                        text=message_text,
                        parse_mode=parse_mode,
                        reply_markup=inline_keyboard
                    )
                
                # Sauvegarder le message envoyé
                sent_messages[channel.channel_id] = message.message_id
                
                # Mettre à jour le statut en DB
                await posts_repo.add_sent_message(post_id, channel.channel_id, message.message_id)
                
            except Exception as e:
                logger.error(f"Erreur envoi vers {channel.channel_id}: {e}")
                failed_channels.append(channel.channel_id)
        
        # Mettre à jour le statut du post
        if sent_messages:
            await posts_repo.set_status(post_id, "sent")
        
        # Afficher le résultat
        success_count = len(sent_messages)
        failed_count = len(failed_channels)
        
        result_text = (
            f"📤 <b>Envoi terminé!</b>\n\n"
            f"✅ <b>Envoyé avec succès:</b> {success_count} canal(x)\n"
        )
        
        if failed_count > 0:
            result_text += f"❌ <b>Échecs:</b> {failed_count} canal(x)\n"
        
        result_text += f"\n🆔 <b>Post ID:</b> <code>{post_id}</code>"
        
        await update.callback_query.edit_message_text(
            result_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur envoi multi-canaux: {e}")
        await update.callback_query.edit_message_text("❌ Erreur lors de l'envoi")


def build_channel_selection_keyboard(post_id: str, channels: List) -> InlineKeyboardMarkup:
    """Construit le clavier de sélection des canaux"""
    keyboard = []
    
    # Boutons pour chaque canal
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"📢 {channel.title or channel.channel_id}",
                callback_data=f"select_channel:{post_id}:{channel.channel_id}"
            )
        ])
    
    # Boutons d'action
    keyboard.append([
        InlineKeyboardButton("✅ Envoyer à tous", callback_data=f"confirm_send:{post_id}:all"),
        InlineKeyboardButton("❌ Annuler", callback_data=f"cancel_send:{post_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def build_post_keyboard(post) -> InlineKeyboardMarkup:
    """Construit le clavier final du post avec réactions et boutons"""
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
