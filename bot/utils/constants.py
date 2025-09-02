"""
Constantes de l'application
"""

from telegram import InlineKeyboardButton


# Emojis
class Emoji:
    """Emojis utilisés dans le bot"""
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    CLOCK = "⏰"
    CALENDAR = "📅"
    SETTINGS = "⚙️"
    CHANNEL = "📢"
    FILE = "📁"
    PHOTO = "🖼️"
    VIDEO = "🎥"
    AUDIO = "🎵"
    DOCUMENT = "📄"
    EDIT = "✏️"
    DELETE = "🗑️"
    SEND = "📤"
    PREVIEW = "👁️"
    BACK = "◀️"
    FORWARD = "▶️"
    UP = "⬆️"
    DOWN = "⬇️"
    STAR = "⭐"
    HEART = "❤️"
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    ROCKET = "🚀"
    LOCK = "🔒"
    UNLOCK = "🔓"
    PIN = "📌"
    GLOBE = "🌍"
    USER = "👤"
    USERS = "👥"
    ROBOT = "🤖"
    SPARKLES = "✨"
    LIGHTNING = "⚡"
    FIRE = "🔥"
    WATER = "💧"
    BELL = "🔔"
    BELL_OFF = "🔕"
    LINK = "🔗"
    CHAIN = "⛓️"
    SHIELD = "🛡️"
    WARNING_SIGN = "⚠️"
    NO_ENTRY = "⛔"
    

# Messages types
class MessageType:
    """Types de messages"""
    START = "start"
    HELP = "help"
    SETTINGS = "settings"
    CHANNELS = "channels"
    POSTS = "posts"
    FILES = "files"
    SCHEDULE = "schedule"
    BROADCAST = "broadcast"
    STATS = "stats"
    ADMIN = "admin"


# Callback data prefixes
class CallbackPrefix:
    """Préfixes pour les callback data"""
    MENU = "menu"
    SETTINGS = "settings"
    CHANNEL = "channel"
    POST = "post"
    FILE = "file"
    SCHEDULE = "schedule"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    DELETE = "delete"
    EDIT = "edit"
    SEND = "send"
    PREVIEW = "preview"
    PAGE = "page"
    REACTION = "reaction"
    URL = "url"
    THUMBNAIL = "thumb"
    RENAME = "rename"
    TIMEZONE = "tz"


# Limites
class Limits:
    """Limites de l'application"""
    MAX_CAPTION_LENGTH = 1024
    MAX_TEXT_LENGTH = 4096
    MAX_FILE_SIZE = 2097152000  # 2GB
    MAX_CHANNELS_PER_USER = 50
    MAX_BUTTONS_PER_ROW = 8
    MAX_BUTTON_ROWS = 100
    MAX_CALLBACK_DATA_LENGTH = 64
    MAX_SCHEDULE_DAYS = 365
    MIN_SCHEDULE_DELAY = 60  # secondes
    MAX_BATCH_SIZE = 100
    MAX_RETRY_ATTEMPTS = 3
    RATE_LIMIT_WINDOW = 60  # secondes
    RATE_LIMIT_MAX_REQUESTS = 30


# Réactions par défaut
DEFAULT_REACTIONS = ["👍", "❤️", "🔥", "👏", "😁", "🤔", "😱", "🤬", "😢", "🎉", "🤩", "🤮"]


# Formats de fichiers supportés
class FileFormats:
    """Formats de fichiers supportés"""
    IMAGE = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]
    VIDEO = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"]
    AUDIO = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"]
    DOCUMENT = [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx"]
    ARCHIVE = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"]
    

# États de conversation
class ConversationState:
    """États pour les ConversationHandler"""
    MAIN_MENU = 0
    WAITING_TEXT = 1
    WAITING_MEDIA = 2
    WAITING_CAPTION = 3
    WAITING_CHANNELS = 4
    WAITING_DATE = 5
    WAITING_TIME = 6
    WAITING_BUTTONS = 7
    WAITING_REACTIONS = 8
    WAITING_THUMBNAIL = 9
    WAITING_RENAME = 10
    WAITING_TIMEZONE = 11
    WAITING_CONFIRMATION = 12
    SETTINGS_MENU = 13
    CHANNELS_MENU = 14
    POSTS_MENU = 15
    FILES_MENU = 16
    SCHEDULE_MENU = 17


# Commandes du bot
class Commands:
    """Commandes disponibles"""
    START = "start"
    HELP = "help"
    SETTINGS = "settings"
    CHANNELS = "channels"
    POST = "post"
    SCHEDULE = "schedule"
    DRAFTS = "drafts"
    FILES = "files"
    STATS = "stats"
    CANCEL = "cancel"
    ADMIN = "admin"
    BROADCAST = "broadcast"
    USERS = "users"
    BACKUP = "backup"


# Messages d'erreur
class ErrorMessages:
    """Messages d'erreur"""
    GENERIC = "❌ Une erreur s'est produite. Veuillez réessayer."
    NOT_AUTHORIZED = "⛔ Vous n'êtes pas autorisé à effectuer cette action."
    INVALID_INPUT = "❌ Entrée invalide. Veuillez vérifier et réessayer."
    FILE_TOO_LARGE = "❌ Le fichier est trop volumineux. Taille max: {size}"
    CHANNEL_NOT_FOUND = "❌ Canal introuvable."
    POST_NOT_FOUND = "❌ Post introuvable."
    NO_CHANNELS = "❌ Vous n'avez pas de canaux configurés."
    RATE_LIMITED = "⚠️ Trop de requêtes. Veuillez patienter."
    DATABASE_ERROR = "❌ Erreur de base de données."
    NETWORK_ERROR = "❌ Erreur réseau. Veuillez réessayer."
    

# Messages de succès
class SuccessMessages:
    """Messages de succès"""
    SAVED = "✅ Enregistré avec succès!"
    SENT = "✅ Envoyé avec succès!"
    DELETED = "✅ Supprimé avec succès!"
    UPDATED = "✅ Mis à jour avec succès!"
    SCHEDULED = "✅ Planifié avec succès!"
    CANCELLED = "✅ Annulé avec succès!"
    

# Textes des boutons
class ButtonText:
    """Textes pour les boutons"""
    BACK = f"{Emoji.BACK} Retour"
    CANCEL = f"{Emoji.CROSS} Annuler"
    CONFIRM = f"{Emoji.CHECK} Confirmer"
    DELETE = f"{Emoji.DELETE} Supprimer"
    EDIT = f"{Emoji.EDIT} Modifier"
    SEND = f"{Emoji.SEND} Envoyer"
    PREVIEW = f"{Emoji.PREVIEW} Aperçu"
    SETTINGS = f"{Emoji.SETTINGS} Paramètres"
    HELP = f"{Emoji.INFO} Aide"
    ADD = "➕ Ajouter"
    REMOVE = "➖ Retirer"
    NEXT = f"Suivant {Emoji.FORWARD}"
    PREVIOUS = f"{Emoji.BACK} Précédent"
    YES = f"{Emoji.CHECK} Oui"
    NO = f"{Emoji.CROSS} Non"
