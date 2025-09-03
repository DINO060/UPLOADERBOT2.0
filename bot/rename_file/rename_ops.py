from __future__ import annotations
import os
from telegram.ext import CallbackContext

from bot.publications.media_handler import send_file_smart
from bot.logger import setup_logger

logger = setup_logger(__name__)


async def download_and_upload_with_thumbnail(
    context: CallbackContext,
    file_id: str,
    new_filename: str,
    thumbnail_path: str | None,
    chat_id: int | str,
    post_type: str,
):
    """
    Télécharge un fichier depuis Telegram et le renvoie avec un nouveau nom et thumbnail
    """
    try:
        file = await context.bot.get_file(file_id)
        downloaded_path = await file.download_to_drive()
        
        new_path = os.path.join(
            os.path.dirname(downloaded_path),
            new_filename
        )
        os.rename(downloaded_path, new_path)
        
        msg = await send_file_smart(
            context_or_app=context,
            chat_id=chat_id,
            file_path=new_path,
            caption=f"📎 {new_filename}",
            thumb_path=thumbnail_path,
            file_name=new_filename,
            is_photo=(post_type == 'photo'),
            is_video=(post_type == 'video'),
            force_document=(post_type == 'document'),
        )
        
        try:
            os.remove(new_path)
        except Exception:
            pass
        
        return msg
        
    except Exception as e:
        logger.error(f"Erreur dans download_and_upload_with_thumbnail: {e}")
        return None


