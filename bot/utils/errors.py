"""
Exceptions personnalisées
"""

from typing import Optional


class BotError(Exception):
    """Exception de base pour le bot"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.user_message = user_message or "Une erreur s'est produite"
        self.error_code = error_code
        super().__init__(self.message)


class DatabaseError(BotError):
    """Erreur de base de données"""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(
            message,
            user_message or "Erreur de base de données",
            "DB_ERROR"
        )


class ValidationError(BotError):
    """Erreur de validation"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(
            message,
            f"Validation échouée: {message}",
            "VALIDATION_ERROR"
        )


class AuthorizationError(BotError):
    """Erreur d'autorisation"""
    
    def __init__(self, message: str = "Non autorisé"):
        super().__init__(
            message,
            "Vous n'êtes pas autorisé à effectuer cette action",
            "AUTH_ERROR"
        )


class RateLimitError(BotError):
    """Erreur de limite de taux"""
    
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limited for {retry_after} seconds",
            f"Trop de requêtes. Réessayez dans {retry_after} secondes",
            "RATE_LIMIT"
        )


class ChannelError(BotError):
    """Erreur liée aux canaux"""
    
    def __init__(self, message: str, channel_id: Optional[int] = None):
        self.channel_id = channel_id
        super().__init__(
            message,
            "Erreur avec le canal",
            "CHANNEL_ERROR"
        )


class PostError(BotError):
    """Erreur liée aux posts"""
    
    def __init__(self, message: str, post_id: Optional[str] = None):
        self.post_id = post_id
        super().__init__(
            message,
            "Erreur avec le post",
            "POST_ERROR"
        )


class FileError(BotError):
    """Erreur liée aux fichiers"""
    
    def __init__(self, message: str, file_id: Optional[str] = None):
        self.file_id = file_id
        super().__init__(
            message,
            "Erreur avec le fichier",
            "FILE_ERROR"
        )


class ScheduleError(BotError):
    """Erreur liée à la planification"""
    
    def __init__(self, message: str, job_id: Optional[str] = None):
        self.job_id = job_id
        super().__init__(
            message,
            "Erreur de planification",
            "SCHEDULE_ERROR"
        )


class QuotaExceededError(BotError):
    """Erreur de dépassement de quota"""
    
    def __init__(self, resource: str, limit: int, current: int):
        self.resource = resource
        self.limit = limit
        self.current = current
        super().__init__(
            f"Quota exceeded for {resource}: {current}/{limit}",
            f"Limite atteinte pour {resource}: {current}/{limit}",
            "QUOTA_EXCEEDED"
        )


class NetworkError(BotError):
    """Erreur réseau"""
    
    def __init__(self, message: str):
        super().__init__(
            message,
            "Erreur de connexion réseau",
            "NETWORK_ERROR"
        )


class ConfigurationError(BotError):
    """Erreur de configuration"""
    
    def __init__(self, message: str):
        super().__init__(
            message,
            "Erreur de configuration",
            "CONFIG_ERROR"
        )


class UserBannedError(BotError):
    """Erreur utilisateur banni"""
    
    def __init__(self, user_id: int, reason: Optional[str] = None):
        self.user_id = user_id
        self.reason = reason
        message = f"User {user_id} is banned"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            "Votre compte a été banni",
            "USER_BANNED"
        )


class ForceSubscribeError(BotError):
    """Erreur de force subscribe"""
    
    def __init__(self, channel: str):
        self.channel = channel
        super().__init__(
            f"User must join {channel}",
            f"Vous devez rejoindre {channel} pour utiliser ce bot",
            "FORCE_SUBSCRIBE"
        )


def handle_error(error: Exception, logger=None) -> str:
    """
    Gère une erreur et retourne un message utilisateur approprié
    
    Args:
        error: L'exception à gérer
        logger: Logger optionnel pour enregistrer l'erreur
    
    Returns:
        Message à afficher à l'utilisateur
    """
    if logger:
        logger.error(f"Error: {type(error).__name__}: {str(error)}")
    
    if isinstance(error, BotError):
        return error.user_message
    
    # Erreurs Telegram
    if "Flood control exceeded" in str(error):
        return "⚠️ Trop de messages. Veuillez patienter."
    
    if "Chat not found" in str(error):
        return "❌ Canal introuvable. Vérifiez que le bot est admin."
    
    if "Message not modified" in str(error):
        return "ℹ️ Aucune modification nécessaire."
    
    if "Message to delete not found" in str(error):
        return "❌ Message introuvable."
    
    if "Bot was blocked by the user" in str(error):
        return "❌ Le bot a été bloqué par l'utilisateur."
    
    # Erreur générique
    return "❌ Une erreur inattendue s'est produite. Veuillez réessayer."
