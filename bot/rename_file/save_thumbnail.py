"""
Module pour sauvegarder et gérer les thumbnails
"""

from typing import Optional
from telegram import Update, PhotoSize
from telegram.ext import ContextTypes

from ..db.repositories.files_repo import FilesRepository
from ..models.file import File, FileType
from ..utils.fileops import create_thumbnail, save_file, delete_file
from ..utils.queues import thumbnail_queue, Task, QueuePriority
from ..logger import setup_logger

logger = setup_logger(__name__)


class ThumbnailManager:
    """Gère les thumbnails des utilisateurs"""
    
    def __init__(self, files_repo: FilesRepository):
        self.files_repo = files_repo
        self.temp_dir = "temp/thumbnails"
    
    async def save_thumbnail(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[str]:
        """
        Sauvegarde un thumbnail depuis un message
        
        Args:
            update: Update Telegram
            context: Contexte
        
        Returns:
            file_id du thumbnail sauvegardé
        """
        message = update.message
        if not message or not message.photo:
            return None
        
        try:
            user_id = update.effective_user.id
            
            # Prendre la plus petite photo (thumbnail)
            photo: PhotoSize = message.photo[0]
            file_id = photo.file_id
            
            # Supprimer l'ancien thumbnail s'il existe
            old_thumbnail = await self.files_repo.get_thumbnail(user_id)
            if old_thumbnail:
                await self.files_repo.delete_file(old_thumbnail.file_id)
                logger.info(f"Ancien thumbnail supprimé pour l'utilisateur {user_id}")
            
            # Sauvegarder le nouveau thumbnail
            success = await self.files_repo.save_thumbnail(
                user_id=user_id,
                file_id=file_id,
                file_name=f"thumb_{user_id}.jpg"
            )
            
            if success:
                logger.info(f"Thumbnail sauvegardé pour l'utilisateur {user_id}: {file_id}")
                
                # Ajouter une tâche de génération de thumbnail optimisé
                await self._queue_thumbnail_optimization(user_id, file_id)
                
                return file_id
            
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du thumbnail: {e}")
            return None
    
    async def get_user_thumbnail(self, user_id: int) -> Optional[str]:
        """
        Récupère le thumbnail d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            file_id du thumbnail ou None
        """
        try:
            thumbnail = await self.files_repo.get_thumbnail(user_id)
            if thumbnail:
                return thumbnail.file_id
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du thumbnail: {e}")
            return None
    
    async def delete_user_thumbnail(self, user_id: int) -> bool:
        """
        Supprime le thumbnail d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            True si supprimé
        """
        try:
            thumbnail = await self.files_repo.get_thumbnail(user_id)
            if thumbnail:
                success = await self.files_repo.delete_file(thumbnail.file_id)
                if success:
                    logger.info(f"Thumbnail supprimé pour l'utilisateur {user_id}")
                return success
            
            return False
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du thumbnail: {e}")
            return False
    
    async def generate_video_thumbnail(
        self,
        video_file_id: str,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[str]:
        """
        Génère un thumbnail depuis une vidéo
        
        Args:
            video_file_id: ID du fichier vidéo
            user_id: ID de l'utilisateur
            context: Contexte
        
        Returns:
            file_id du thumbnail généré
        """
        try:
            # Télécharger la vidéo temporairement
            file = await context.bot.get_file(video_file_id)
            video_path = f"{self.temp_dir}/video_{user_id}.mp4"
            await file.download_to_drive(video_path)
            
            # Extraire une frame avec OpenCV
            import cv2
            cap = cv2.VideoCapture(video_path)
            
            # Prendre la première frame
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Sauvegarder la frame comme image
                thumb_path = f"{self.temp_dir}/thumb_{user_id}.jpg"
                cv2.imwrite(thumb_path, frame)
                
                # Créer un thumbnail optimisé
                optimized_path = f"{self.temp_dir}/thumb_opt_{user_id}.jpg"
                await create_thumbnail(thumb_path, optimized_path, (320, 320))
                
                # Uploader le thumbnail
                with open(optimized_path, 'rb') as f:
                    message = await context.bot.send_photo(
                        chat_id=user_id,
                        photo=f,
                        caption="Thumbnail généré depuis la vidéo"
                    )
                
                # Sauvegarder le file_id
                if message.photo:
                    file_id = message.photo[-1].file_id
                    await self.files_repo.save_thumbnail(
                        user_id=user_id,
                        file_id=file_id,
                        file_name=f"video_thumb_{user_id}.jpg"
                    )
                    
                    # Supprimer le message
                    await message.delete()
                    
                    # Nettoyer les fichiers temporaires
                    delete_file(video_path)
                    delete_file(thumb_path)
                    delete_file(optimized_path)
                    
                    logger.info(f"Thumbnail vidéo généré pour l'utilisateur {user_id}")
                    return file_id
            
            # Nettoyer en cas d'échec
            delete_file(video_path)
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du thumbnail vidéo: {e}")
            return None
    
    async def _queue_thumbnail_optimization(
        self,
        user_id: int,
        file_id: str
    ):
        """
        Ajoute une tâche d'optimisation de thumbnail à la queue
        
        Args:
            user_id: ID de l'utilisateur
            file_id: ID du fichier
        """
        try:
            task = Task(
                task_id=f"thumb_opt_{user_id}_{file_id[:8]}",
                user_id=user_id,
                task_type="add_thumbnail",
                data={
                    "file_id": file_id,
                    "user_id": user_id,
                    "size": (320, 320)
                },
                priority=QueuePriority.LOW
            )
            
            await thumbnail_queue.add_task(task)
            logger.info(f"Tâche d'optimisation ajoutée pour {user_id}")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à la queue: {e}")
    
    async def apply_thumbnail_to_document(
        self,
        document_file_id: str,
        thumbnail_file_id: str,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Applique un thumbnail à un document
        
        Args:
            document_file_id: ID du document
            thumbnail_file_id: ID du thumbnail
            context: Contexte
        
        Returns:
            True si appliqué
        """
        # Note: Telegram ne permet pas de modifier le thumbnail d'un fichier existant
        # Cette fonction est principalement pour la documentation
        # Le thumbnail doit être défini lors de l'envoi initial du document
        
        logger.warning("Les thumbnails doivent être définis lors de l'envoi du document")
        return False
    
    def get_thumbnail_info(self, thumbnail: File) -> dict:
        """
        Obtient les informations d'un thumbnail
        
        Args:
            thumbnail: Objet File du thumbnail
        
        Returns:
            Dict avec les infos
        """
        return {
            "file_id": thumbnail.file_id,
            "file_size": thumbnail.size_formatted,
            "created_at": thumbnail.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "dimensions": f"{thumbnail.width}x{thumbnail.height}" if thumbnail.width else "Unknown"
        }
