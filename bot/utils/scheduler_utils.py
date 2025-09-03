from __future__ import annotations
from typing import Dict, Any, Optional
from telegram.ext import Application

from bot.publications.media_handler import send_file_smart
from bot.db.motor_client import get_database
from bot.db.repositories.posts_repo import PostsRepository
from bot.logger import setup_logger

logger = setup_logger(__name__)


async def send_scheduled_file(post: Dict[str, Any], app: Optional[Application] = None) -> bool:
    """
    Envoie un post planifié avec la logique smart
    """
    try:
        logger.info(f"📤 Envoi du post planifié: {post.get('id')}")
        
        channel_id = post.get('channel_id')
        post_type = post.get('post_type', 'text')
        content = post.get('content')
        caption = post.get('caption', '')
        
        db = await get_database()
        channel = await db.channels.find_one({"_id": int(channel_id)})
        if not channel:
            logger.error(f"❌ Canal non trouvé: {channel_id}")
            return False
        
        target = channel.get("username") or channel_id
        
        if post_type == 'text':
            m = await app.bot.send_message(
                chat_id=target,
                text=content,
                parse_mode="HTML"
            )
        else:
            file_path = content if isinstance(content, str) else content.get("path")
            m = await send_file_smart(
                context_or_app=app,
                chat_id=target,
                file_path=file_path,
                caption=caption,
                is_photo=(post_type == 'photo'),
                is_video=(post_type == 'video'),
                force_document=(post_type == 'document')
            )
        
        if m:
            posts_repo = PostsRepository(db)
            await posts_repo.mark_as_published(
                post['id'],
                {target: getattr(m, "message_id", None)}
            )
            logger.info("✅ Post planifié envoyé avec succès")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur dans send_scheduled_file: {e}")
        return False


