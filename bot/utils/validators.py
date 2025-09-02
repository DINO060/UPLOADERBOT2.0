"""
Validateurs pour les entrées utilisateur
"""

import re
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .errors import ValidationError
from .constants import Limits, FileFormats


def validate_channel_id(channel_id: str) -> int:
    """
    Valide un ID de canal
    
    Args:
        channel_id: ID du canal (string)
    
    Returns:
        ID du canal (int)
    
    Raises:
        ValidationError: Si l'ID est invalide
    """
    try:
        # Accepte les formats: -100xxxxx, @username
        if channel_id.startswith("@"):
            return channel_id  # Username, sera résolu plus tard
        
        # Conversion en int
        channel_id_int = int(channel_id)
        
        # Vérifier que c'est un supergroupe/canal (commence par -100)
        if channel_id_int > -100:
            raise ValidationError("ID de canal invalide")
        
        return channel_id_int
    except (ValueError, TypeError):
        raise ValidationError(f"Format d'ID de canal invalide: {channel_id}")


def validate_username(username: str) -> str:
    """
    Valide un username Telegram
    
    Args:
        username: Username à valider
    
    Returns:
        Username validé
    
    Raises:
        ValidationError: Si le username est invalide
    """
    # Retirer le @ s'il est présent
    if username.startswith("@"):
        username = username[1:]
    
    # Vérifier le format
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$", username):
        raise ValidationError(
            "Username invalide. Doit commencer par une lettre et contenir 5-32 caractères"
        )
    
    return username


def validate_caption(caption: str) -> str:
    """
    Valide une légende
    
    Args:
        caption: Légende à valider
    
    Returns:
        Légende validée et tronquée si nécessaire
    """
    if not caption:
        return ""
    
    # Tronquer si trop long
    if len(caption) > Limits.MAX_CAPTION_LENGTH:
        caption = caption[:Limits.MAX_CAPTION_LENGTH-3] + "..."
    
    return caption.strip()


def validate_text(text: str) -> str:
    """
    Valide un texte de message
    
    Args:
        text: Texte à valider
    
    Returns:
        Texte validé et tronqué si nécessaire
    """
    if not text:
        raise ValidationError("Le texte ne peut pas être vide")
    
    # Tronquer si trop long
    if len(text) > Limits.MAX_TEXT_LENGTH:
        text = text[:Limits.MAX_TEXT_LENGTH-3] + "..."
    
    return text.strip()


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Valide la taille d'un fichier
    
    Args:
        file_size: Taille du fichier en bytes
        max_size: Taille maximale autorisée (par défaut: Limits.MAX_FILE_SIZE)
    
    Returns:
        True si valide
    
    Raises:
        ValidationError: Si le fichier est trop gros
    """
    max_size = max_size or Limits.MAX_FILE_SIZE
    
    if file_size > max_size:
        size_mb = max_size / (1024 * 1024)
        raise ValidationError(f"Fichier trop volumineux. Taille max: {size_mb:.0f} MB")
    
    return True


def validate_file_extension(filename: str, allowed_types: Optional[List[str]] = None) -> bool:
    """
    Valide l'extension d'un fichier
    
    Args:
        filename: Nom du fichier
        allowed_types: Types autorisés (si None, tous sont autorisés)
    
    Returns:
        True si valide
    
    Raises:
        ValidationError: Si l'extension n'est pas autorisée
    """
    if not allowed_types:
        return True
    
    ext = get_file_extension(filename).lower()
    if ext not in allowed_types:
        raise ValidationError(f"Type de fichier non autorisé: {ext}")
    
    return True


def get_file_extension(filename: str) -> str:
    """
    Extrait l'extension d'un fichier
    
    Args:
        filename: Nom du fichier
    
    Returns:
        Extension (avec le point)
    """
    if not filename or "." not in filename:
        return ""
    
    return "." + filename.split(".")[-1].lower()


def validate_url(url: str) -> str:
    """
    Valide une URL
    
    Args:
        url: URL à valider
    
    Returns:
        URL validée
    
    Raises:
        ValidationError: Si l'URL est invalide
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError("URL invalide")
        
        if result.scheme not in ["http", "https", "tg"]:
            raise ValidationError("Protocole non supporté")
        
        return url
    except Exception:
        raise ValidationError(f"URL invalide: {url}")


def validate_schedule_time(schedule_time: datetime) -> datetime:
    """
    Valide un temps de planification
    
    Args:
        schedule_time: Temps à valider
    
    Returns:
        Temps validé
    
    Raises:
        ValidationError: Si le temps est invalide
    """
    now = datetime.utcnow()
    
    # Vérifier que ce n'est pas dans le passé (avec 1 minute de tolérance)
    if schedule_time < now - timedelta(minutes=1):
        raise ValidationError("Impossible de planifier dans le passé")
    
    # Vérifier que ce n'est pas trop loin dans le futur
    max_future = now + timedelta(days=Limits.MAX_SCHEDULE_DAYS)
    if schedule_time > max_future:
        raise ValidationError(f"Impossible de planifier au-delà de {Limits.MAX_SCHEDULE_DAYS} jours")
    
    # Vérifier le délai minimum
    min_time = now + timedelta(seconds=Limits.MIN_SCHEDULE_DELAY)
    if schedule_time < min_time:
        raise ValidationError(f"Délai minimum: {Limits.MIN_SCHEDULE_DELAY} secondes")
    
    return schedule_time


def validate_timezone(timezone: str) -> str:
    """
    Valide un fuseau horaire
    
    Args:
        timezone: Fuseau horaire à valider
    
    Returns:
        Fuseau horaire validé
    
    Raises:
        ValidationError: Si le fuseau est invalide
    """
    import pytz
    
    try:
        pytz.timezone(timezone)
        return timezone
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValidationError(f"Fuseau horaire inconnu: {timezone}")


def validate_cron_expression(expression: str) -> str:
    """
    Valide une expression cron
    
    Args:
        expression: Expression cron à valider
    
    Returns:
        Expression validée
    
    Raises:
        ValidationError: Si l'expression est invalide
    """
    from croniter import croniter
    
    try:
        croniter(expression)
        return expression
    except Exception as e:
        raise ValidationError(f"Expression cron invalide: {str(e)}")


def validate_callback_data(data: str) -> str:
    """
    Valide les données de callback
    
    Args:
        data: Données à valider
    
    Returns:
        Données validées
    
    Raises:
        ValidationError: Si les données sont invalides
    """
    if len(data) > Limits.MAX_CALLBACK_DATA_LENGTH:
        raise ValidationError(
            f"Callback data trop long. Max: {Limits.MAX_CALLBACK_DATA_LENGTH} caractères"
        )
    
    return data


def validate_buttons(buttons: List[List[dict]]) -> List[List[dict]]:
    """
    Valide une structure de boutons inline
    
    Args:
        buttons: Structure de boutons
    
    Returns:
        Boutons validés
    
    Raises:
        ValidationError: Si la structure est invalide
    """
    if len(buttons) > Limits.MAX_BUTTON_ROWS:
        raise ValidationError(f"Trop de lignes de boutons. Max: {Limits.MAX_BUTTON_ROWS}")
    
    for row in buttons:
        if len(row) > Limits.MAX_BUTTONS_PER_ROW:
            raise ValidationError(f"Trop de boutons par ligne. Max: {Limits.MAX_BUTTONS_PER_ROW}")
        
        for button in row:
            if "text" not in button:
                raise ValidationError("Chaque bouton doit avoir un texte")
            
            if "url" in button:
                validate_url(button["url"])
            elif "callback_data" in button:
                validate_callback_data(button["callback_data"])
            else:
                raise ValidationError("Chaque bouton doit avoir une URL ou callback_data")
    
    return buttons


def parse_datetime(text: str, timezone: str = "UTC") -> datetime:
    """
    Parse une date/heure depuis du texte
    
    Args:
        text: Texte à parser
        timezone: Fuseau horaire
    
    Returns:
        datetime parsé
    
    Raises:
        ValidationError: Si le format est invalide
    """
    import pytz
    from dateutil import parser
    
    try:
        # Essayer de parser avec dateutil
        dt = parser.parse(text)
        
        # Ajouter le timezone si pas présent
        if dt.tzinfo is None:
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
        
        # Convertir en UTC
        return dt.astimezone(pytz.UTC)
    except Exception:
        raise ValidationError(f"Format de date/heure invalide: {text}")
