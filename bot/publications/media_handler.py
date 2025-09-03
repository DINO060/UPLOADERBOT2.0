from __future__ import annotations
import os
from pathlib import Path
from typing import Union, Optional

from telegram import InputFile, Message
from telegram.ext import Application

from bot.clients.pyrogram_client import get_pyro_client
from bot.logger import setup_logger

logger = setup_logger(__name__)

SIZE_THRESHOLD = 50 * 1024 * 1024  # 50MB


async def send_file_smart(
    context_or_app,
    chat_id: Union[int, str],
    file_path: str,
    caption: str = "",
    thumb_path: Optional[str] = None,
    file_name: Optional[str] = None,
    is_photo: bool = False,
    is_video: bool = False,
    force_document: bool = False,
    reply_markup=None,
    disable_notification: bool = False,
) -> Union[Message, None]:
    """
    Envoie un fichier de manière intelligente:
      - ≤ 50 MB: Bot API (plus rapide)
      - > 50 MB: Pyrogram
    """
    try:
        if (not os.path.exists(file_path)) or os.path.getsize(file_path) == 0:
            raise Exception("Le fichier est vide ou corrompu.")

        file_size = os.path.getsize(file_path)
        logger.info(f"📤 Envoi du fichier: {file_path} ({file_size} bytes)")

        if file_size <= SIZE_THRESHOLD:
            logger.info("⚡ Utilisation Bot API")
            return await _send_with_bot_api(
                context_or_app, chat_id, file_path, caption, thumb_path,
                file_name, is_photo, is_video, force_document,
                reply_markup, disable_notification
            )
        else:
            logger.info("🔥 Utilisation Pyrogram")
            return await _send_with_pyrogram(
                chat_id, file_path, caption, thumb_path,
                file_name, is_photo, is_video, force_document,
                reply_markup
            )

    except Exception as e:
        logger.error(f"❌ ERREUR send_file_smart: {e}")
        return None


def _extract_bot(context_or_app):
    if hasattr(context_or_app, "bot"):
        return context_or_app.bot
    if isinstance(context_or_app, Application):
        return context_or_app.bot
    return context_or_app


async def _send_with_bot_api(
    context_or_app,
    chat_id: Union[int, str],
    file_path: str,
    caption: str,
    thumb_path: Optional[str],
    file_name: Optional[str],
    is_photo: bool,
    is_video: bool,
    force_document: bool,
    reply_markup,
    disable_notification: bool,
) -> Message:
    bot = _extract_bot(context_or_app)
    caption = caption or ""

    def _input_file(path: str, name: Optional[str]) -> InputFile:
        return InputFile(path, filename=name) if name else InputFile(path)

    thumb_if = InputFile(thumb_path) if (thumb_path and os.path.exists(thumb_path)) else None

    if is_photo and not force_document:
        return await bot.send_photo(
            chat_id=chat_id,
            photo=_input_file(file_path, None),
            caption=caption,
            reply_markup=reply_markup,
            disable_notification=disable_notification,
            parse_mode="HTML",
        )

    if is_video and not force_document:
        return await bot.send_video(
            chat_id=chat_id,
            video=_input_file(file_path, file_name),
            caption=caption,
            thumbnail=thumb_if,
            reply_markup=reply_markup,
            disable_notification=disable_notification,
            supports_streaming=True,
            parse_mode="HTML",
        )

    return await bot.send_document(
        chat_id=chat_id,
        document=_input_file(file_path, file_name),
        caption=caption,
        thumbnail=thumb_if,
        reply_markup=reply_markup,
        disable_notification=disable_notification,
        parse_mode="HTML",
    )


async def _send_with_pyrogram(
    chat_id: Union[int, str],
    file_path: str,
    caption: str,
    thumb_path: Optional[str],
    file_name: Optional[str],
    is_photo: bool,
    is_video: bool,
    force_document: bool,
    reply_markup,
) -> Message:
    from pyrogram.types import InlineKeyboardMarkup

    if os.path.getsize(file_path) == 0:
        raise Exception("The file to send is empty (0 B). Check the source file.")

    pyro = await get_pyro_client()

    send_kwargs = {
        "chat_id": chat_id,
        "caption": caption or "",
    }
    if file_name:
        send_kwargs["file_name"] = file_name
    if thumb_path and os.path.exists(thumb_path):
        send_kwargs["thumb"] = thumb_path
    if reply_markup and isinstance(reply_markup, InlineKeyboardMarkup):
        send_kwargs["reply_markup"] = reply_markup

    if is_photo and not force_document:
        msg = await pyro.send_photo(photo=file_path, **send_kwargs)
    elif is_video and not force_document:
        msg = await pyro.send_video(video=file_path, **send_kwargs)
    else:
        msg = await pyro.send_document(document=file_path, **send_kwargs)

    logger.info(f"✅ Fichier envoyé via Pyrogram: {file_name or Path(file_path).name}")
    return msg


