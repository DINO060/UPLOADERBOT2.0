"""
Module pour envoyer les posts vers les canaux
"""

from typing import Dict, List, Optional, Any
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest, Forbidden

from ..models.post import Post, PostType, PostStatus
from ..models.channel import Channel
from ..db.repositories.posts_repo import PostsRepository
from ..db.repositories.channels_repo import ChannelsRepository
from ..utils.throttling import message_throttler
from ..logger import setup_logger

logger = setup_logger(__name__)


class PostSender:
    """Gère l'envoi des posts vers les canaux"""
    
    def __init__(
        self,
        bot: Bot,
        posts_repo: PostsRepository,
        channels_repo: ChannelsRepository
    ):
        self.bot = bot
        self.posts_repo = posts_repo
        self.channels_repo = channels_repo
    
    async def send_post(
        self,
        post: Post,
        test_mode: bool = False
    ) -> Dict[int, int]:
        """
        Envoie un post vers les canaux
        
        Args:
            post: Post à envoyer
            test_mode: Si True, envoie uniquement à l'utilisateur
        
        Returns:
            Dict channel_id -> message_id des messages envoyés
        """
        message_ids = {}
        
        try:
            # Marquer comme en cours d'envoi
            await self.posts_repo.update_post(
                post._id,
                {"status": PostStatus.PUBLISHING}
            )
            
            # Préparer le markup si nécessaire
            reply_markup = self._build_reply_markup(post)
            
            # Obtenir les canaux de destination
            if test_mode:
                # Mode test: envoyer à l'utilisateur
                channel_ids = [post.user_id]
            else:
                channel_ids = post.channel_ids
            
            # Envoyer vers chaque canal
            for channel_id in channel_ids:
                try:
                    # Vérifier que le canal est actif
                    if not test_mode:
                        channel = await self.channels_repo.get_channel(channel_id)
                        if not channel or not channel.is_active:
                            logger.warning(f"Canal {channel_id} inactif ou introuvable")
                            continue
                    
                    # Throttling pour éviter le flood
                    await message_throttler.wait_if_needed(channel_id)
                    
                    # Envoyer selon le type
                    message_id = await self._send_by_type(
                        channel_id,
                        post,
                        reply_markup
                    )
                    
                    if message_id:
                        message_ids[channel_id] = message_id
                        logger.info(f"Post envoyé au canal {channel_id}: {message_id}")
                    
                except (BadRequest, Forbidden) as e:
                    logger.error(f"Erreur Telegram pour le canal {channel_id}: {e}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi au canal {channel_id}: {e}")
            
            # Mettre à jour le statut
            if message_ids:
                await self.posts_repo.mark_as_published(post._id, message_ids)
                logger.info(f"Post {post._id} publié dans {len(message_ids)} canaux")
            else:
                await self.posts_repo.update_post(
                    post._id,
                    {"status": PostStatus.FAILED}
                )
                logger.error(f"Échec de la publication du post {post._id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du post: {e}")
            await self.posts_repo.update_post(
                post._id,
                {"status": PostStatus.FAILED, "error": str(e)}
            )
        
        return message_ids
    
    async def _send_by_type(
        self,
        chat_id: int,
        post: Post,
        reply_markup: Optional[InlineKeyboardMarkup]
    ) -> Optional[int]:
        """
        Envoie selon le type de post
        
        Args:
            chat_id: ID du chat/canal
            post: Post à envoyer
            reply_markup: Boutons inline
        
        Returns:
            ID du message envoyé
        """
        try:
            message = None
            
            if post.content_type == PostType.TEXT:
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=post.text,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    disable_web_page_preview=post.disable_web_page_preview,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.PHOTO:
                message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.VIDEO:
                message = await self.bot.send_video(
                    chat_id=chat_id,
                    video=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.AUDIO:
                message = await self.bot.send_audio(
                    chat_id=chat_id,
                    audio=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.DOCUMENT:
                message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.ANIMATION:
                message = await self.bot.send_animation(
                    chat_id=chat_id,
                    animation=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.VOICE:
                message = await self.bot.send_voice(
                    chat_id=chat_id,
                    voice=post.file_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.VIDEO_NOTE:
                message = await self.bot.send_video_note(
                    chat_id=chat_id,
                    video_note=post.file_id,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content,
                    reply_markup=reply_markup
                )
            
            elif post.content_type == PostType.MEDIA_GROUP:
                # Pour les media groups, on doit construire la liste des médias
                media = await self._build_media_group(post)
                messages = await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=media,
                    disable_notification=post.disable_notification,
                    protect_content=post.protect_content
                )
                # Retourner l'ID du premier message
                if messages:
                    message = messages[0]
            
            return message.message_id if message else None
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            return None
    
    async def _build_media_group(self, post: Post) -> List[Any]:
        """
        Construit un media group
        
        Args:
            post: Post contenant les médias
        
        Returns:
            Liste des InputMedia
        """
        from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument
        
        media = []
        
        for i, file_id in enumerate(post.file_ids):
            # Déterminer le type (simplifié, peut être amélioré)
            # En production, on devrait stocker le type de chaque fichier
            
            # Ajouter la légende seulement au premier élément
            caption = post.caption if i == 0 else None
            parse_mode = post.parse_mode if i == 0 else None
            
            # Par défaut, on considère que c'est une photo
            # À améliorer avec une vraie détection du type
            media.append(InputMediaPhoto(
                media=file_id,
                caption=caption,
                parse_mode=parse_mode
            ))
        
        return media
    
    def _build_reply_markup(self, post: Post) -> Optional[InlineKeyboardMarkup]:
        """
        Construit le markup des boutons inline
        
        Args:
            post: Post contenant les boutons
        
        Returns:
            InlineKeyboardMarkup ou None
        """
        if not post.inline_buttons:
            return None
        
        keyboard = []
        
        for row in post.inline_buttons:
            button_row = []
            for button_data in row:
                button = InlineKeyboardButton(
                    text=button_data.get("text", "Button"),
                    url=button_data.get("url"),
                    callback_data=button_data.get("callback_data")
                )
                button_row.append(button)
            
            if button_row:
                keyboard.append(button_row)
        
        return InlineKeyboardMarkup(keyboard) if keyboard else None
    
    async def edit_post(
        self,
        chat_id: int,
        message_id: int,
        post: Post
    ) -> bool:
        """
        Édite un post existant
        
        Args:
            chat_id: ID du chat/canal
            message_id: ID du message
            post: Post avec les nouvelles données
        
        Returns:
            True si édité avec succès
        """
        try:
            reply_markup = self._build_reply_markup(post)
            
            if post.content_type == PostType.TEXT:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=post.text,
                    parse_mode=post.parse_mode,
                    disable_web_page_preview=post.disable_web_page_preview,
                    reply_markup=reply_markup
                )
            else:
                # Pour les médias, on ne peut éditer que la légende
                await self.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=post.caption,
                    parse_mode=post.parse_mode,
                    reply_markup=reply_markup
                )
            
            logger.info(f"Post édité: {chat_id}/{message_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'édition: {e}")
            return False
    
    async def delete_post(
        self,
        chat_id: int,
        message_id: int
    ) -> bool:
        """
        Supprime un post
        
        Args:
            chat_id: ID du chat/canal
            message_id: ID du message
        
        Returns:
            True si supprimé
        """
        try:
            await self.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
            logger.info(f"Post supprimé: {chat_id}/{message_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False
