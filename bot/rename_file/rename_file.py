"""
Module pour renommer et réuploader des fichiers
"""

from typing import Optional, Tuple
from telegram import Update, Document, InputFile
from telegram.ext import ContextTypes
import os
import tempfile

from ..db.repositories.files_repo import FilesRepository
from ..models.file import File, FileType
from ..utils.fileops import sanitize_filename, get_mime_type, get_file_size
from ..utils.validators import validate_file_size, get_file_extension
from ..logger import setup_logger

logger = setup_logger(__name__)


class FileRenamer:
    """Gère le renommage et réupload de fichiers"""
    
    def __init__(self, files_repo: FilesRepository):
        self.files_repo = files_repo
        self.temp_dir = tempfile.gettempdir()
    
    async def rename_and_send(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        original_file_id: str,
        new_name: str,
        thumbnail_file_id: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Optional[str]:
        """
        Renomme et renvoie un fichier
        
        Args:
            update: Update Telegram
            context: Contexte
            original_file_id: ID du fichier original
            new_name: Nouveau nom
            thumbnail_file_id: ID du thumbnail (optionnel)
            caption: Légende (optionnel)
        
        Returns:
            file_id du nouveau fichier
        """
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Nettoyer le nom de fichier
            new_name = sanitize_filename(new_name)
            
            # Télécharger le fichier original
            file = await context.bot.get_file(original_file_id)
            
            # Créer un chemin temporaire avec le nouveau nom
            temp_path = os.path.join(self.temp_dir, new_name)
            
            # Télécharger vers le chemin temporaire
            await file.download_to_drive(temp_path)
            
            # Vérifier la taille
            file_size = get_file_size(temp_path)
            validate_file_size(file_size)
            
            # Préparer le thumbnail si fourni
            thumb = None
            if thumbnail_file_id:
                thumb_file = await context.bot.get_file(thumbnail_file_id)
                thumb_path = os.path.join(self.temp_dir, f"thumb_{user_id}.jpg")
                await thumb_file.download_to_drive(thumb_path)
                thumb = open(thumb_path, 'rb')
            
            # Envoyer le fichier renommé
            with open(temp_path, 'rb') as f:
                message = await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=new_name,
                    thumbnail=thumb,
                    caption=caption,
                    parse_mode="HTML"
                )
            
            # Fermer et nettoyer le thumbnail
            if thumb:
                thumb.close()
                os.remove(thumb_path)
            
            # Nettoyer le fichier temporaire
            os.remove(temp_path)
            
            # Récupérer le nouveau file_id
            if message.document:
                new_file_id = message.document.file_id
                
                # Sauvegarder dans la DB
                file_obj = File(
                    file_id=new_file_id,
                    user_id=user_id,
                    file_type=FileType.DOCUMENT,
                    file_name=new_name,
                    file_size=file_size,
                    mime_type=get_mime_type(new_name),
                    custom_name=new_name
                )
                await self.files_repo.save_file(file_obj)
                
                logger.info(f"Fichier renommé et envoyé: {new_name}")
                return new_file_id
            
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors du renommage: {e}")
            # Nettoyer en cas d'erreur
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return None
    
    async def batch_rename(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        file_ids: list,
        rename_pattern: str
    ) -> Tuple[int, int]:
        """
        Renomme plusieurs fichiers en batch
        
        Args:
            update: Update Telegram
            context: Contexte
            file_ids: Liste des file_ids
            rename_pattern: Pattern de renommage (ex: "document_{n}.pdf")
        
        Returns:
            Tuple (succès, échecs)
        """
        success_count = 0
        fail_count = 0
        
        for i, file_id in enumerate(file_ids, 1):
            try:
                # Générer le nouveau nom
                new_name = rename_pattern.format(n=i, index=i-1)
                
                # Renommer et envoyer
                result = await self.rename_and_send(
                    update,
                    context,
                    file_id,
                    new_name
                )
                
                if result:
                    success_count += 1
                else:
                    fail_count += 1
                
                # Pause pour éviter le flood
                import asyncio
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Erreur lors du renommage batch: {e}")
                fail_count += 1
        
        logger.info(f"Renommage batch terminé: {success_count} succès, {fail_count} échecs")
        return success_count, fail_count
    
    async def add_prefix_suffix(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        file_id: str,
        prefix: str = "",
        suffix: str = ""
    ) -> Optional[str]:
        """
        Ajoute un préfixe/suffixe au nom du fichier
        
        Args:
            update: Update Telegram
            context: Contexte
            file_id: ID du fichier
            prefix: Préfixe à ajouter
            suffix: Suffixe à ajouter (avant l'extension)
        
        Returns:
            file_id du fichier renommé
        """
        try:
            # Récupérer les infos du fichier
            file = await self.files_repo.get_file(file_id)
            if not file or not file.file_name:
                # Essayer de récupérer depuis Telegram
                tg_file = await context.bot.get_file(file_id)
                original_name = os.path.basename(tg_file.file_path) if tg_file.file_path else "file"
            else:
                original_name = file.file_name
            
            # Séparer nom et extension
            name_without_ext, ext = os.path.splitext(original_name)
            
            # Construire le nouveau nom
            new_name = f"{prefix}{name_without_ext}{suffix}{ext}"
            
            # Renommer et envoyer
            return await self.rename_and_send(
                update,
                context,
                file_id,
                new_name
            )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout prefix/suffix: {e}")
            return None
    
    async def change_extension(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        file_id: str,
        new_extension: str
    ) -> Optional[str]:
        """
        Change l'extension d'un fichier
        
        Args:
            update: Update Telegram
            context: Contexte
            file_id: ID du fichier
            new_extension: Nouvelle extension (avec ou sans point)
        
        Returns:
            file_id du fichier avec nouvelle extension
        """
        try:
            # Ajouter le point si nécessaire
            if not new_extension.startswith('.'):
                new_extension = '.' + new_extension
            
            # Récupérer le nom original
            file = await self.files_repo.get_file(file_id)
            if not file or not file.file_name:
                tg_file = await context.bot.get_file(file_id)
                original_name = os.path.basename(tg_file.file_path) if tg_file.file_path else "file.bin"
            else:
                original_name = file.file_name
            
            # Changer l'extension
            name_without_ext, _ = os.path.splitext(original_name)
            new_name = name_without_ext + new_extension
            
            # Renommer et envoyer
            return await self.rename_and_send(
                update,
                context,
                file_id,
                new_name
            )
        
        except Exception as e:
            logger.error(f"Erreur lors du changement d'extension: {e}")
            return None
    
    async def auto_rename_by_type(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        file_id: str
    ) -> Optional[str]:
        """
        Renomme automatiquement selon le type de fichier
        
        Args:
            update: Update Telegram
            context: Contexte
            file_id: ID du fichier
        
        Returns:
            file_id du fichier renommé
        """
        try:
            user_id = update.effective_user.id
            
            # Télécharger temporairement pour analyser
            file = await context.bot.get_file(file_id)
            temp_path = os.path.join(self.temp_dir, f"temp_{user_id}")
            await file.download_to_drive(temp_path)
            
            # Déterminer le type MIME
            mime_type = get_mime_type(temp_path)
            
            # Générer un nom basé sur le type
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Mapper le MIME vers une extension et un préfixe
            mime_map = {
                "image/jpeg": ("photo", ".jpg"),
                "image/png": ("image", ".png"),
                "video/mp4": ("video", ".mp4"),
                "audio/mpeg": ("audio", ".mp3"),
                "application/pdf": ("document", ".pdf"),
                "application/zip": ("archive", ".zip"),
            }
            
            prefix, ext = mime_map.get(mime_type, ("file", ""))
            if not ext:
                # Essayer de garder l'extension originale
                _, ext = os.path.splitext(file.file_path) if file.file_path else ("", "")
            
            new_name = f"{prefix}_{timestamp}{ext}"
            
            # Nettoyer le fichier temporaire
            os.remove(temp_path)
            
            # Renommer et envoyer
            return await self.rename_and_send(
                update,
                context,
                file_id,
                new_name
            )
        
        except Exception as e:
            logger.error(f"Erreur lors du renommage automatique: {e}")
            # Nettoyer en cas d'erreur
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return None
