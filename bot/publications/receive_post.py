"""
Module pour recevoir et stocker les posts (drafts)
"""

from typing import Optional, List
from telegram import Update, Message
from telegram.ext import ContextTypes

from ..models.post import Post, PostType, PostStatus
from ..models.file import File, FileType
from ..db.repositories.posts_repo import PostsRepository
from ..db.repositories.files_repo import FilesRepository
from ..utils.validators import validate_caption, validate_file_size
from ..logger import setup_logger

logger = setup_logger(__name__)


class PostReceiver:
    """Gère la réception et l'enregistrement des posts"""
    
    def __init__(self, posts_repo: PostsRepository, files_repo: FilesRepository):
        self.posts_repo = posts_repo
        self.files_repo = files_repo
    
    async def receive_text_post(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        channel_ids: List[int]
    ) -> Optional[str]:
        """
        Reçoit un post texte
        
        Args:
            update: Update Telegram
            context: Contexte
            channel_ids: IDs des canaux de destination
        
        Returns:
            ID du post créé
        """
        message = update.message
        if not message or not message.text:
            return None
        
        try:
            user_id = update.effective_user.id
            
            # Créer le post
            post = Post(
                user_id=user_id,
                channel_ids=channel_ids,
                content_type=PostType.TEXT,
                text=message.text,
                parse_mode=message.parse_mode or "HTML",
                status=PostStatus.DRAFT
            )
            
            # Sauvegarder
            post_id = await self.posts_repo.create_post(post)
            logger.info(f"Post texte créé: {post_id}")
            
            return post_id
        
        except Exception as e:
            logger.error(f"Erreur lors de la réception du post texte: {e}")
            return None
    
    async def receive_media_post(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        channel_ids: List[int]
    ) -> Optional[str]:
        """
        Reçoit un post avec média
        
        Args:
            update: Update Telegram
            context: Contexte
            channel_ids: IDs des canaux de destination
        
        Returns:
            ID du post créé
        """
        message = update.message
        if not message:
            return None
        
        try:
            user_id = update.effective_user.id
            post_type = None
            file_id = None
            file_info = None
            
            # Déterminer le type de média
            if message.photo:
                post_type = PostType.PHOTO
                file_info = message.photo[-1]  # Plus grande résolution
                file_id = file_info.file_id
            elif message.video:
                post_type = PostType.VIDEO
                file_info = message.video
                file_id = file_info.file_id
            elif message.audio:
                post_type = PostType.AUDIO
                file_info = message.audio
                file_id = file_info.file_id
            elif message.document:
                post_type = PostType.DOCUMENT
                file_info = message.document
                file_id = file_info.file_id
            elif message.animation:
                post_type = PostType.ANIMATION
                file_info = message.animation
                file_id = file_info.file_id
            elif message.voice:
                post_type = PostType.VOICE
                file_info = message.voice
                file_id = file_info.file_id
            elif message.video_note:
                post_type = PostType.VIDEO_NOTE
                file_info = message.video_note
                file_id = file_info.file_id
            else:
                return None
            
            # Valider la taille
            if hasattr(file_info, 'file_size'):
                validate_file_size(file_info.file_size)
            
            # Créer le post
            post = Post(
                user_id=user_id,
                channel_ids=channel_ids,
                content_type=post_type,
                file_id=file_id,
                caption=validate_caption(message.caption or ""),
                parse_mode=message.caption_parse_mode or "HTML",
                status=PostStatus.DRAFT
            )
            
            # Sauvegarder le fichier dans la DB
            if file_info:
                file = File(
                    file_id=file_id,
                    user_id=user_id,
                    file_type=self._get_file_type(post_type),
                    file_name=getattr(file_info, 'file_name', None),
                    file_size=getattr(file_info, 'file_size', 0),
                    mime_type=getattr(file_info, 'mime_type', None),
                    width=getattr(file_info, 'width', None),
                    height=getattr(file_info, 'height', None),
                    duration=getattr(file_info, 'duration', None)
                )
                await self.files_repo.save_file(file)
            
            # Sauvegarder le post
            post_id = await self.posts_repo.create_post(post)
            logger.info(f"Post média créé: {post_id} (type: {post_type})")
            
            return post_id
        
        except Exception as e:
            logger.error(f"Erreur lors de la réception du post média: {e}")
            return None
    
    async def receive_media_group(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        channel_ids: List[int],
        messages: List[Message]
    ) -> Optional[str]:
        """
        Reçoit un groupe de médias
        
        Args:
            update: Update Telegram
            context: Contexte
            channel_ids: IDs des canaux
            messages: Messages du groupe
        
        Returns:
            ID du post créé
        """
        if not messages:
            return None
        
        try:
            user_id = update.effective_user.id
            file_ids = []
            
            # Collecter tous les file_ids
            for msg in messages:
                if msg.photo:
                    file_ids.append(msg.photo[-1].file_id)
                elif msg.video:
                    file_ids.append(msg.video.file_id)
                elif msg.document:
                    file_ids.append(msg.document.file_id)
            
            if not file_ids:
                return None
            
            # Récupérer la légende du premier message
            caption = messages[0].caption if messages[0].caption else ""
            
            # Créer le post
            post = Post(
                user_id=user_id,
                channel_ids=channel_ids,
                content_type=PostType.MEDIA_GROUP,
                file_ids=file_ids,
                caption=validate_caption(caption),
                parse_mode=messages[0].caption_parse_mode or "HTML",
                status=PostStatus.DRAFT
            )
            
            # Sauvegarder les fichiers
            for msg in messages:
                file_info = None
                file_id = None
                file_type = FileType.OTHER
                
                if msg.photo:
                    file_info = msg.photo[-1]
                    file_id = file_info.file_id
                    file_type = FileType.PHOTO
                elif msg.video:
                    file_info = msg.video
                    file_id = file_info.file_id
                    file_type = FileType.VIDEO
                elif msg.document:
                    file_info = msg.document
                    file_id = file_info.file_id
                    file_type = FileType.DOCUMENT
                
                if file_info:
                    file = File(
                        file_id=file_id,
                        user_id=user_id,
                        file_type=file_type,
                        file_name=getattr(file_info, 'file_name', None),
                        file_size=getattr(file_info, 'file_size', 0),
                        mime_type=getattr(file_info, 'mime_type', None)
                    )
                    await self.files_repo.save_file(file)
            
            # Sauvegarder le post
            post_id = await self.posts_repo.create_post(post)
            logger.info(f"Media group créé: {post_id} ({len(file_ids)} fichiers)")
            
            return post_id
        
        except Exception as e:
            logger.error(f"Erreur lors de la réception du media group: {e}")
            return None
    
    async def update_post_caption(
        self,
        post_id: str,
        caption: str
    ) -> bool:
        """
        Met à jour la légende d'un post
        
        Args:
            post_id: ID du post
            caption: Nouvelle légende
        
        Returns:
            True si mis à jour
        """
        try:
            caption = validate_caption(caption)
            success = await self.posts_repo.update_post(
                post_id,
                {"caption": caption}
            )
            
            if success:
                logger.info(f"Légende mise à jour pour le post {post_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la légende: {e}")
            return False
    
    async def add_thumbnail_to_post(
        self,
        post_id: str,
        thumbnail_file_id: str
    ) -> bool:
        """
        Ajoute un thumbnail à un post
        
        Args:
            post_id: ID du post
            thumbnail_file_id: ID du fichier thumbnail
        
        Returns:
            True si ajouté
        """
        try:
            success = await self.posts_repo.update_post(
                post_id,
                {"thumbnail_id": thumbnail_file_id}
            )
            
            if success:
                logger.info(f"Thumbnail ajouté au post {post_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du thumbnail: {e}")
            return False
    
    def _get_file_type(self, post_type: str) -> str:
        """
        Convertit un PostType en FileType
        
        Args:
            post_type: Type de post
        
        Returns:
            Type de fichier correspondant
        """
        mapping = {
            PostType.PHOTO: FileType.PHOTO,
            PostType.VIDEO: FileType.VIDEO,
            PostType.AUDIO: FileType.AUDIO,
            PostType.DOCUMENT: FileType.DOCUMENT,
            PostType.ANIMATION: FileType.ANIMATION,
            PostType.VOICE: FileType.VOICE,
            PostType.VIDEO_NOTE: FileType.VIDEO_NOTE
        }
        return mapping.get(post_type, FileType.OTHER)
