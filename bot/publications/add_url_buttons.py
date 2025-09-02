"""
Module pour ajouter des boutons URL aux posts
"""

from typing import List, Dict, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..models.post import Post
from ..db.repositories.posts_repo import PostsRepository
from ..utils.validators import validate_url, validate_buttons
from ..logger import setup_logger

logger = setup_logger(__name__)


class URLButtonsManager:
    """Gère l'ajout de boutons URL aux posts"""
    
    def __init__(self, posts_repo: PostsRepository):
        self.posts_repo = posts_repo
    
    async def add_url_buttons(
        self,
        post_id: str,
        buttons: List[List[Dict[str, str]]]
    ) -> bool:
        """
        Ajoute des boutons URL à un post
        
        Args:
            post_id: ID du post
            buttons: Structure des boutons [[{text, url}]]
        
        Returns:
            True si ajouté avec succès
        """
        try:
            # Valider les boutons
            buttons = validate_buttons(buttons)
            
            # Mettre à jour le post
            success = await self.posts_repo.update_post(
                post_id,
                {"inline_buttons": buttons}
            )
            
            if success:
                logger.info(f"Boutons URL ajoutés au post {post_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des boutons: {e}")
            return False
    
    def parse_buttons_text(self, text: str) -> List[List[Dict[str, str]]]:
        """
        Parse un texte pour extraire les boutons
        Format: [Texte](url) ou [Texte](url) | [Texte2](url2) pour la même ligne
        
        Args:
            text: Texte contenant les boutons
        
        Returns:
            Structure des boutons
        """
        buttons = []
        lines = text.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            row = []
            # Séparer les boutons sur la même ligne
            button_texts = line.split('|')
            
            for button_text in button_texts:
                button_text = button_text.strip()
                
                # Extraire le texte et l'URL
                import re
                match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', button_text)
                
                if match:
                    text = match.group(1).strip()
                    url = match.group(2).strip()
                    
                    try:
                        # Valider l'URL
                        url = validate_url(url)
                        row.append({"text": text, "url": url})
                    except:
                        logger.warning(f"URL invalide ignorée: {url}")
            
            if row:
                buttons.append(row)
        
        return buttons
    
    def build_url_keyboard(
        self,
        buttons: List[List[Dict[str, str]]]
    ) -> InlineKeyboardMarkup:
        """
        Construit un clavier avec des boutons URL
        
        Args:
            buttons: Structure des boutons
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []
        
        for row in buttons:
            button_row = []
            for button_data in row:
                button = InlineKeyboardButton(
                    text=button_data["text"],
                    url=button_data["url"]
                )
                button_row.append(button)
            
            if button_row:
                keyboard.append(button_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def add_quick_buttons(
        self,
        post_id: str,
        button_type: str
    ) -> bool:
        """
        Ajoute des boutons prédéfinis rapidement
        
        Args:
            post_id: ID du post
            button_type: Type de boutons (share, channel, etc.)
        
        Returns:
            True si ajouté
        """
        buttons = []
        
        if button_type == "share":
            # Bouton de partage
            buttons = [[{
                "text": "📤 Partager",
                "url": f"https://t.me/share/url?url=https://t.me/{post_id}"
            }]]
        
        elif button_type == "channel":
            # Bouton vers le canal
            from ..config import Config
            config = Config()
            if config.FORCE_SUB_CHANNEL:
                channel = config.FORCE_SUB_CHANNEL
                if channel.startswith("@"):
                    buttons = [[{
                        "text": "📢 Notre canal",
                        "url": f"https://t.me/{channel[1:]}"
                    }]]
        
        elif button_type == "bot":
            # Bouton vers le bot
            from ..config import Config
            config = Config()
            if config.BOT_USERNAME:
                buttons = [[{
                    "text": "🤖 Utiliser le bot",
                    "url": f"https://t.me/{config.BOT_USERNAME}"
                }]]
        
        elif button_type == "website":
            # Bouton vers un site web
            buttons = [[{
                "text": "🌐 Site Web",
                "url": "https://example.com"
            }]]
        
        if buttons:
            return await self.add_url_buttons(post_id, buttons)
        
        return False
    
    async def combine_with_reactions(
        self,
        post: Post,
        reactions_keyboard: InlineKeyboardMarkup
    ) -> InlineKeyboardMarkup:
        """
        Combine les boutons URL avec les réactions
        
        Args:
            post: Post contenant les boutons URL
            reactions_keyboard: Clavier des réactions
        
        Returns:
            Clavier combiné
        """
        keyboard = []
        
        # Ajouter d'abord les boutons URL
        if post.inline_buttons:
            for row in post.inline_buttons:
                button_row = []
                for button_data in row:
                    button = InlineKeyboardButton(
                        text=button_data["text"],
                        url=button_data.get("url"),
                        callback_data=button_data.get("callback_data")
                    )
                    button_row.append(button)
                
                if button_row:
                    keyboard.append(button_row)
        
        # Ajouter une ligne de séparation (optionnel)
        # keyboard.append([InlineKeyboardButton("─" * 20, callback_data="separator")])
        
        # Ajouter les réactions
        if reactions_keyboard and reactions_keyboard.inline_keyboard:
            keyboard.extend(reactions_keyboard.inline_keyboard)
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_navigation_buttons(
        self,
        current_page: int,
        total_pages: int,
        callback_prefix: str
    ) -> List[List[Dict[str, str]]]:
        """
        Crée des boutons de navigation
        
        Args:
            current_page: Page actuelle
            total_pages: Nombre total de pages
            callback_prefix: Préfixe pour les callbacks
        
        Returns:
            Structure de boutons de navigation
        """
        buttons = []
        nav_row = []
        
        # Bouton précédent
        if current_page > 1:
            nav_row.append({
                "text": "◀️ Précédent",
                "callback_data": f"{callback_prefix}:page:{current_page-1}"
            })
        
        # Indicateur de page
        nav_row.append({
            "text": f"📄 {current_page}/{total_pages}",
            "callback_data": f"{callback_prefix}:page:current"
        })
        
        # Bouton suivant
        if current_page < total_pages:
            nav_row.append({
                "text": "Suivant ▶️",
                "callback_data": f"{callback_prefix}:page:{current_page+1}"
            })
        
        if nav_row:
            buttons.append(nav_row)
        
        return buttons
    
    def create_confirmation_buttons(
        self,
        callback_prefix: str,
        confirm_text: str = "✅ Confirmer",
        cancel_text: str = "❌ Annuler"
    ) -> List[List[Dict[str, str]]]:
        """
        Crée des boutons de confirmation
        
        Args:
            callback_prefix: Préfixe pour les callbacks
            confirm_text: Texte du bouton confirmer
            cancel_text: Texte du bouton annuler
        
        Returns:
            Structure de boutons
        """
        return [[
            {
                "text": confirm_text,
                "callback_data": f"{callback_prefix}:confirm"
            },
            {
                "text": cancel_text,
                "callback_data": f"{callback_prefix}:cancel"
            }
        ]]
