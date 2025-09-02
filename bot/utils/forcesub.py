"""
Middleware pour forcer l'abonnement à un canal
"""

from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import BaseHandler, ContextTypes
from telegram.error import BadRequest, Forbidden

from logger import setup_logger
from utils.errors import ForceSubscribeError

logger = setup_logger(__name__)


class ForceSubscribeMiddleware(BaseHandler):
    """Middleware pour vérifier l'abonnement forcé"""
    
    def __init__(self, channel: str):
        """
        Initialise le middleware
        
        Args:
            channel: Username ou ID du canal
        """
        super().__init__(self.handle_update)
        self.channel = channel
        self._channel_id: Optional[int] = None
        self._channel_username: Optional[str] = None
        
        # Parser le canal
        if channel.startswith("@"):
            self._channel_username = channel
        else:
            try:
                self._channel_id = int(channel)
            except ValueError:
                self._channel_username = f"@{channel}"
    
    async def handle_update(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Vérifie si l'utilisateur est abonné au canal
        
        Args:
            update: Update Telegram
            context: Contexte
        
        Returns:
            True si l'utilisateur est abonné ou exemptéå
        """
        # Ignorer les updates sans message ou utilisateur
        if not update.effective_user:
            return True
        
        # Ignorer les mises à jour de canaux/groupes
        if update.effective_chat and update.effective_chat.type != "private":
            return True
        
        user_id = update.effective_user.id
        
        # Vérifier si l'utilisateur est admin/owner (exemptés)
        from config import Config
        config = Config()
        if user_id in config.ADMIN_IDS or user_id == config.OWNER_ID:
            return True
        
        # Vérifier l'abonnement
        is_subscribed = await self.check_subscription(user_id, context)
        
        if not is_subscribed:
            await self.send_force_sub_message(update, context)
            return False
        
        return True
    
    async def check_subscription(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Vérifie si un utilisateur est abonné au canal
        
        Args:
            user_id: ID de l'utilisateur
            context: Contexte
        
        Returns:
            True si abonné
        """
        try:
            # Utiliser l'ID ou le username
            channel_ref = self._channel_id or self._channel_username
            
            # Obtenir le membre du canal
            member = await context.bot.get_chat_member(
                chat_id=channel_ref,
                user_id=user_id
            )
            
            # Vérifier le statut
            return member.status in [
                "creator",
                "administrator",
                "member"
            ]
        except (BadRequest, Forbidden):
            logger.error(f"Impossible de vérifier l'abonnement pour {user_id}")
            return True  # En cas d'erreur, on laisse passer
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return True
    
    async def send_force_sub_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Envoie le message de force subscribe
        
        Args:
            update: Update Telegram
            context: Contexte
        """
        channel_link = self._channel_username or f"https://t.me/c/{str(self._channel_id)[4:]}"
        
        text = (
            "🔒 <b>Abonnement requis</b>\n\n"
            f"Pour utiliser ce bot, vous devez d'abord vous abonner à notre canal.\n\n"
            f"👉 Rejoignez {channel_link}\n\n"
            "Puis cliquez sur le bouton ci-dessous pour vérifier votre abonnement."
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Rejoindre le canal",
                    url=f"https://t.me/{self._channel_username[1:]}" if self._channel_username else channel_link
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ J'ai rejoint",
                    callback_data="check_subscription"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.answer(
                "❌ Vous devez d'abord rejoindre le canal!",
                show_alert=True
            )


async def check_force_subscribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    channel: str
) -> bool:
    """
    Fonction helper pour vérifier l'abonnement
    
    Args:
        update: Update Telegram
        context: Contexte
        channel: Canal à vérifier
    
    Returns:
        True si l'utilisateur est abonné
    """
    if not update.effective_user:
        return True
    
    user_id = update.effective_user.id
    
    # Vérifier si l'utilisateur est admin/owner
    from ..config import Config
    config = Config()
    if user_id in config.ADMIN_IDS or user_id == config.OWNER_ID:
        return True
    
    try:
        member = await context.bot.get_chat_member(
            chat_id=channel,
            user_id=user_id
        )
        
        return member.status in ["creator", "administrator", "member"]
    except:
        return True  # En cas d'erreur, on laisse passer


async def handle_check_subscription_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Gère le callback de vérification d'abonnement
    
    Args:
        update: Update Telegram
        context: Contexte
    """
    query = update.callback_query
    await query.answer()
    
    from ..config import Config
    config = Config()
    
    if not config.FORCE_SUB_CHANNEL:
        return
    
    # Vérifier l'abonnement
    is_subscribed = await check_force_subscribe(
        update,
        context,
        config.FORCE_SUB_CHANNEL
    )
    
    if is_subscribed:
        # L'utilisateur est maintenant abonné
        text = (
            "✅ <b>Merci!</b>\n\n"
            "Votre abonnement a été vérifié avec succès.\n"
            "Vous pouvez maintenant utiliser toutes les fonctionnalités du bot.\n\n"
            "Tapez /start pour commencer."
        )
        
        await query.edit_message_text(
            text,
            parse_mode="HTML"
        )
    else:
        # L'utilisateur n'est toujours pas abonné
        await query.answer(
            "❌ Vous n'êtes pas encore abonné au canal!",
            show_alert=True
        )
