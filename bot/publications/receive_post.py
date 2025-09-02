"""
Handler pour la réception et création de drafts
"""

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from typing import Optional

from config import Config
from logger import setup_logger
from models.post import Post, PostType
from db.repositories.posts_repo import PostsRepository
from db.motor_client import get_database

logger = setup_logger(__name__)
config = Config()


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les messages texte pour créer un draft"""
    await create_draft_from_message(update, context, PostType.TEXT)


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les photos pour créer un draft"""
    await create_draft_from_message(update, context, PostType.PHOTO)


async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les vidéos pour créer un draft"""
    await create_draft_from_message(update, context, PostType.VIDEO)


async def handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les documents pour créer un draft"""
    await create_draft_from_message(update, context, PostType.DOCUMENT)


async def handle_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les audios pour créer un draft"""
    await create_draft_from_message(update, context, PostType.AUDIO)


async def handle_animation_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les animations (GIF) pour créer un draft"""
    await create_draft_from_message(update, context, PostType.ANIMATION)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les messages vocaux pour créer un draft"""
    await create_draft_from_message(update, context, PostType.VOICE)


async def handle_video_note_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les vidéo notes pour créer un draft"""
    await create_draft_from_message(update, context, PostType.VIDEO_NOTE)


async def create_draft_from_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    content_type: PostType
) -> None:
    """Crée un draft à partir d'un message"""
    try:
        message = update.message
        if not message:
            return
        
        user_id = message.from_user.id
        
        # Préparer les données du post
        post_data = {
            "user_id": user_id,
            "channel_ids": [],  # Sera rempli plus tard lors de la sélection
            "content_type": content_type.value,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Récupérer le contenu selon le type
        file_id = None
        text = None
        caption = None
        
        if content_type == PostType.TEXT:
            text = message.text
            post_data["text"] = text
            
        elif content_type == PostType.PHOTO:
            # Prendre la photo de meilleure qualité (dernière dans la liste)
            photo = message.photo[-1] if message.photo else None
            if photo:
                file_id = photo.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                
        elif content_type == PostType.VIDEO:
            if message.video:
                file_id = message.video.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                # Sauvegarder aussi le thumbnail s'il existe
                if message.video.thumbnail:
                    post_data["thumbnail_id"] = message.video.thumbnail.file_id
                    
        elif content_type == PostType.DOCUMENT:
            if message.document:
                file_id = message.document.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                # Sauvegarder le nom du fichier dans metadata
                post_data["metadata"] = {
                    "file_name": message.document.file_name,
                    "mime_type": message.document.mime_type,
                    "file_size": message.document.file_size
                }
                
        elif content_type == PostType.AUDIO:
            if message.audio:
                file_id = message.audio.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                # Metadata audio
                post_data["metadata"] = {
                    "performer": message.audio.performer,
                    "title": message.audio.title,
                    "duration": message.audio.duration
                }
                
        elif content_type == PostType.ANIMATION:
            if message.animation:
                file_id = message.animation.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                
        elif content_type == PostType.VOICE:
            if message.voice:
                file_id = message.voice.file_id
                caption = message.caption
                post_data["file_id"] = file_id
                post_data["caption"] = caption
                post_data["metadata"] = {
                    "duration": message.voice.duration
                }
                
        elif content_type == PostType.VIDEO_NOTE:
            if message.video_note:
                file_id = message.video_note.file_id
                post_data["file_id"] = file_id
                post_data["metadata"] = {
                    "duration": message.video_note.duration,
                    "length": message.video_note.length
                }
        
        # Créer le post en DB
        post = Post(**post_data)
        
        # Sauvegarder en DB (en mode test, on simule)
        try:
            db = await get_database()
            posts_repo = PostsRepository(db)
            post_id = await posts_repo.create_post(post)
            logger.info(f"Draft créé avec ID: {post_id}")
            
            # Répondre à l'utilisateur
            response = (
                f"📝 **Draft créé avec succès!**\n\n"
                f"🆔 **ID:** `{post_id}`\n"
                f"📄 **Type:** {content_type.value}\n"
                f"📊 **Status:** draft\n\n"
                f"_Utilisez /send {post_id} pour envoyer ce post_"
            )
            
        except Exception as db_error:
            # En cas d'erreur DB, on crée un ID temporaire
            import uuid
            temp_id = str(uuid.uuid4())[:8]
            logger.warning(f"Mode test - Draft simulé avec ID: {temp_id}")
            
            response = (
                f"📝 **Draft créé (mode test)!**\n\n"
                f"🆔 **ID:** `{temp_id}`\n"
                f"📄 **Type:** {content_type.value}\n"
                f"📊 **Status:** draft\n\n"
                f"⚠️ _MongoDB non connecté - draft temporaire_"
            )
        
        await message.reply_text(
            response,
            parse_mode="Markdown"
        )
        
        # Log le contenu pour debug
        content_preview = ""
        if text:
            content_preview = text[:50] + ("..." if len(text) > 50 else "")
        elif caption:
            content_preview = caption[:50] + ("..." if len(caption) > 50 else "")
        elif file_id:
            content_preview = f"[Media: {file_id[:20]}...]"
            
        logger.info(
            f"Draft créé - User: {user_id}, Type: {content_type.value}, "
            f"Content: {content_preview}"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du draft: {e}")
        await message.reply_text(
            "❌ Une erreur est survenue lors de la création du draft.",
            parse_mode="Markdown"
        )


async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les groupes de médias (albums)"""
    try:
        message = update.message
        if not message or not message.media_group_id:
            return
        
        # Stocker les médias du groupe dans le contexte utilisateur
        user_data = context.user_data
        media_group_id = message.media_group_id
        
        if "media_groups" not in user_data:
            user_data["media_groups"] = {}
        
        if media_group_id not in user_data["media_groups"]:
            user_data["media_groups"][media_group_id] = {
                "messages": [],
                "timestamp": datetime.utcnow()
            }
        
        # Ajouter ce message au groupe
        user_data["media_groups"][media_group_id]["messages"].append(message)
        
        # Attendre un peu pour collecter tous les messages du groupe
        # (PTB les envoie un par un)
        await context.application.job_queue.run_once(
            process_media_group,
            when=1,  # Attendre 1 seconde
            data={
                "user_id": message.from_user.id,
                "media_group_id": media_group_id,
                "chat_id": message.chat_id
            },
            name=f"media_group_{media_group_id}"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du groupe de médias: {e}")


async def process_media_group(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traite un groupe de médias complet"""
    try:
        job_data = context.job.data
        user_id = job_data["user_id"]
        media_group_id = job_data["media_group_id"]
        chat_id = job_data["chat_id"]
        
        # Récupérer les médias du groupe
        user_data = context.application.user_data.get(user_id, {})
        media_groups = user_data.get("media_groups", {})
        media_group = media_groups.get(media_group_id)
        
        if not media_group:
            return
        
        messages = media_group["messages"]
        
        # Créer un draft pour le groupe
        file_ids = []
        caption = None
        
        for msg in messages:
            if msg.photo:
                file_ids.append(msg.photo[-1].file_id)
            elif msg.video:
                file_ids.append(msg.video.file_id)
            
            # Prendre la première caption trouvée
            if not caption and msg.caption:
                caption = msg.caption
        
        # Créer le post
        post_data = {
            "user_id": user_id,
            "channel_ids": [],
            "content_type": PostType.MEDIA_GROUP.value,
            "file_ids": file_ids,
            "caption": caption,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        post = Post(**post_data)
        
        # Sauvegarder en DB
        try:
            db = await get_database()
            posts_repo = PostsRepository(db)
            post_id = await posts_repo.create_post(post)
            
            response = (
                f"📸 **Album créé avec succès!**\n\n"
                f"🆔 **ID:** `{post_id}`\n"
                f"📄 **Type:** media_group\n"
                f"🖼️ **Médias:** {len(file_ids)}\n"
                f"📊 **Status:** draft\n\n"
                f"_Utilisez /send {post_id} pour envoyer cet album_"
            )
        except:
            import uuid
            temp_id = str(uuid.uuid4())[:8]
            response = (
                f"📸 **Album créé (mode test)!**\n\n"
                f"🆔 **ID:** `{temp_id}`\n"
                f"🖼️ **Médias:** {len(file_ids)}\n"
                f"⚠️ _MongoDB non connecté_"
            )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=response,
            parse_mode="Markdown"
        )
        
        # Nettoyer le groupe de la mémoire
        del media_groups[media_group_id]
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du groupe de médias: {e}")