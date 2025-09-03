"""
Fonctions utilitaires helper (micro-snippets)
"""

from typing import Dict, Any, Optional, Tuple, List
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import Application

from ..logger import setup_logger

logger = setup_logger(__name__)


def extract_content(msg: Message) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Récupère content_type + content d'un message
    
    Args:
        msg: Message Telegram
    
    Returns:
        Tuple (content_type, content_dict)
    """
    if msg.text:
        # text_html n'est pas toujours présent selon la version PTB
        text_value = getattr(msg, "text_html", None) or msg.text
        return "text", {"text": text_value}
    
    if msg.photo:
        return "photo", {
            "file_id": msg.photo[-1].file_id,
            "caption": msg.caption or ""
        }
    
    if msg.video:
        return "video", {
            "file_id": msg.video.file_id,
            "caption": msg.caption or ""
        }
    
    if msg.document:
        return "document", {
            "file_id": msg.document.file_id,
            "caption": msg.caption or "",
            "file_name": msg.document.file_name
        }
    
    if msg.audio:
        return "audio", {
            "file_id": msg.audio.file_id,
            "caption": msg.caption or "",
            "title": msg.audio.title,
            "performer": msg.audio.performer
        }
    
    if msg.animation:
        return "animation", {
            "file_id": msg.animation.file_id,
            "caption": msg.caption or ""
        }
    
    if msg.voice:
        return "voice", {
            "file_id": msg.voice.file_id,
            "caption": msg.caption or "",
            "duration": msg.voice.duration
        }
    
    if msg.video_note:
        return "video_note", {
            "file_id": msg.video_note.file_id,
            "duration": msg.video_note.duration
        }
    
    if msg.sticker:
        return "sticker", {
            "file_id": msg.sticker.file_id,
            "emoji": msg.sticker.emoji
        }
    
    return None, {}


def build_preview_markup(post: Dict[str, Any]) -> Optional[InlineKeyboardMarkup]:
    """
    Preview keyboard builder (réactions + URL)
    
    Args:
        post: Dictionnaire du post
    
    Returns:
        InlineKeyboardMarkup ou None
    """
    rows: List[List[InlineKeyboardButton]] = []
    
    # Ligne de réactions (format attendu: dict emoji->count)
    reactions = post.get("reactions")
    if isinstance(reactions, dict) and reactions:
        reaction_row: List[InlineKeyboardButton] = []
        for emoji, count in reactions.items():
            button_text = f"{emoji} {count}" if isinstance(count, int) and count > 0 else str(emoji)
            reaction_row.append(
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"react:{emoji}:{post['_id']}"
                )
            )
        if reaction_row:
            rows.append(reaction_row)
    
    # Lignes de boutons URL (liste de lignes, chaque ligne = liste de {text,url})
    url_buttons = post.get("url_buttons")
    if isinstance(url_buttons, list) and url_buttons:
        for button_group in url_buttons:
            url_row: List[InlineKeyboardButton] = []
            for btn in button_group or []:
                url_row.append(
                    InlineKeyboardButton(
                        btn.get("text", "Lien"),
                        url=btn.get("url", "")
                    )
                )
            if url_row:
                rows.append(url_row)
    
    # Boutons de configuration
    config_row: List[InlineKeyboardButton] = []
    if not reactions:
        config_row.append(
            InlineKeyboardButton(
                "👍 Ajouter réactions",
                callback_data=f"add_reactions:{post['_id']}"
            )
        )
    if not url_buttons:
        config_row.append(
            InlineKeyboardButton(
                "🔗 Ajouter boutons",
                callback_data=f"add_buttons:{post['_id']}"
            )
        )
    if config_row:
        rows.append(config_row)
    
    # Boutons d'action
    rows.append([
        InlineKeyboardButton(
            "⏰ Planifier",
            callback_data=f"schedule:{post['_id']}"
        ),
        InlineKeyboardButton(
            "🗑️ Auto-delete",
            callback_data=f"autodel:setup:{post['_id']}"
        )
    ])
    
    return InlineKeyboardMarkup(rows) if rows else None


async def send_now(app: Application, post: Dict[str, Any]) -> List[Tuple[int, int]]:
    """
    Envoi multi-canaux (send now)
    
    Args:
        app: Application PTB
        post: Dictionnaire du post
    
    Returns:
        Liste de tuples (chat_id, message_id)
    """
    bot = app.bot
    markup = build_preview_markup(post)
    sent: List[Tuple[int, int]] = []
    
    for chat_id in post.get("channels", []):
        try:
            ct = post.get("content_type")
            c = post.get("content", {})
            message = None
            
            if ct == "text":
                message = await bot.send_message(
                    chat_id,
                    c.get("text", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "photo":
                message = await bot.send_photo(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "video":
                message = await bot.send_video(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "document":
                message = await bot.send_document(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "audio":
                message = await bot.send_audio(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "animation":
                message = await bot.send_animation(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "voice":
                message = await bot.send_voice(
                    chat_id,
                    c.get("file_id"),
                    caption=c.get("caption", ""),
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            elif ct == "video_note":
                message = await bot.send_video_note(
                    chat_id,
                    c.get("file_id"),
                    reply_markup=markup
                )
            
            if message:
                sent.append((chat_id, message.message_id))
                logger.info(f"Message envoyé: {chat_id}/{message.message_id}")
        except Exception as e:
            logger.error(f"Erreur envoi vers {chat_id}: {e}")
    
    return sent


async def add_sent_message(post_id: str, chat_id: int, message_id: int):
    """
    Enregistre un message envoyé
    
    Args:
        post_id: ID du post
        chat_id: ID du chat/canal
        message_id: ID du message
    """
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        # Récupérer le post
        post = await posts_repo.get_post(post_id)
        if not post:
            return
        
        # Ajouter le message envoyé
        if not post.message_ids:
            post.message_ids = {}
        
        post.message_ids[chat_id] = message_id
        
        # Mettre à jour en DB
        await posts_repo.update_post(
            post_id,
            {"message_ids": post.message_ids}
        )
        
        logger.info(f"Message enregistré: {post_id} -> {chat_id}/{message_id}")
        
    except Exception as e:
        logger.error(f"Erreur add_sent_message: {e}")


async def set_status(post_id: str, status: str):
    """
    Change le statut d'un post
    
    Args:
        post_id: ID du post
        status: Nouveau statut
    """
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        success = await posts_repo.set_status(post_id, status)
        
        if success:
            logger.info(f"Statut mis à jour: {post_id} -> {status}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erreur set_status: {e}")
        return False


async def inc_reaction(post_id: str, emoji: str):
    """
    Incrémente une réaction
    
    Args:
        post_id: ID du post
        emoji: Emoji de la réaction
    """
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        success = await posts_repo.inc_reaction(post_id)
        
        if success:
            logger.info(f"Réaction incrémentée: {post_id} -> {emoji}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erreur inc_reaction: {e}")
        return False


async def add_url_button(post_id: str, text: str, url: str):
    """
    Ajoute un bouton URL au post
    
    Args:
        post_id: ID du post
        text: Texte du bouton
        url: URL du bouton
    """
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        success = await posts_repo.add_url_button(post_id, text, url)
        
        if success:
            logger.info(f"Bouton URL ajouté: {post_id} -> {text}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erreur add_url_button: {e}")
        return False


async def set_scheduled(post_id: str, when_dt):
    """
    Planifie un post
    
    Args:
        post_id: ID du post
        when_dt: Datetime de planification
    """
    try:
        from ..db.motor_client import get_database
        from ..db.repositories.posts_repo import PostsRepository
        
        db = await get_database()
        posts_repo = PostsRepository(db)
        
        success = await posts_repo.update_post(
            post_id,
            {
                "status": "scheduled",
                "scheduled_at": when_dt
            }
        )
        
        if success:
            logger.info(f"Post planifié: {post_id} -> {when_dt}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erreur set_scheduled: {e}")
        return False


