"""
Handler pour l'annulation des opérations
"""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from ..logger import setup_logger

logger = setup_logger(__name__)


async def handle_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande d'annulation"""
    try:
        # Nettoyer le contexte utilisateur
        context.user_data.clear()
        
        # Supprimer le clavier personnalisé si présent
        await update.message.reply_text(
            "❌ <b>Opération annulée</b>\n\n"
            "Toutes les opérations en cours ont été annulées.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Si on est dans une conversation, la terminer
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur cancel: {e}")
        await update.message.reply_text("❌ Erreur lors de l'annulation")


async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère le callback d'annulation"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Nettoyer le contexte
        context.user_data.clear()
        
        # Éditer le message
        await query.edit_message_text(
            "❌ <b>Opération annulée</b>",
            parse_mode="HTML"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur cancel callback: {e}")
        await query.answer("❌ Erreur", show_alert=True)


async def handle_cancel_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule un envoi en cours"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Nettoyer les données d'envoi
        context.user_data.pop('sending_post_id', None)
        context.user_data.pop('selected_channels', None)
        
        await query.edit_message_text(
            "❌ <b>Envoi annulé</b>\n\n"
            "Le post n'a pas été envoyé.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur cancel send: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule une édition en cours"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Nettoyer les données d'édition
        context.user_data.pop('editing_post_id', None)
        context.user_data.pop('edit_field', None)
        
        await query.edit_message_text(
            "❌ <b>Édition annulée</b>\n\n"
            "Les modifications n'ont pas été enregistrées.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur cancel edit: {e}")
        await query.edit_message_text("❌ Erreur")


async def handle_cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule une planification"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Nettoyer les données de planification
        context.user_data.pop('scheduling_post_id', None)
        context.user_data.pop('schedule_time', None)
        
        await query.edit_message_text(
            "❌ <b>Planification annulée</b>\n\n"
            "Le post n'a pas été planifié.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Erreur cancel schedule: {e}")
        await query.edit_message_text("❌ Erreur")


async def reset_user_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Réinitialise complètement l'état de l'utilisateur"""
    try:
        user_id = update.effective_user.id
        
        # Nettoyer toutes les données
        context.user_data.clear()
        context.chat_data.clear()
        
        # Annuler les jobs en cours pour cet utilisateur
        current_jobs = context.job_queue.get_jobs_by_name(str(user_id))
        for job in current_jobs:
            job.schedule_removal()
        
        logger.info(f"État réinitialisé pour l'utilisateur {user_id}")
        
        await update.message.reply_text(
            "🔄 <b>État réinitialisé</b>\n\n"
            "Votre session a été complètement réinitialisée.\n"
            "Utilisez /start pour recommencer.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Erreur reset: {e}")
        await update.message.reply_text("❌ Erreur lors de la réinitialisation")


