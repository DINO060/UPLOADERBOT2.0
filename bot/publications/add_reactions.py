"""
Module pour ajouter des réactions aux posts (style likebot)
"""

from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..models.post import Post
from ..db.repositories.posts_repo import PostsRepository
from ..utils.constants import DEFAULT_REACTIONS
from ..logger import setup_logger

logger = setup_logger(__name__)


class ReactionsManager:
    """Gère les réactions sur les posts"""
    
    def __init__(self, posts_repo: PostsRepository):
        self.posts_repo = posts_repo
        self.reaction_counts = {}  # Cache des compteurs
    
    async def add_reactions_to_post(
        self,
        post: Post,
        reactions: Optional[List[str]] = None
    ) -> bool:
        """
        Ajoute des réactions à un post
        
        Args:
            post: Post concerné
            reactions: Liste des réactions (emojis)
        
        Returns:
            True si ajouté avec succès
        """
        try:
            # Utiliser les réactions par défaut si non spécifiées
            if not reactions:
                reactions = DEFAULT_REACTIONS[:6]  # Limiter à 6 réactions
            
            # Mettre à jour le post
            success = await self.posts_repo.update_post(
                post._id,
                {"reactions": reactions}
            )
            
            if success:
                # Initialiser les compteurs
                for reaction in reactions:
                    self._init_reaction_count(post._id, reaction)
                
                logger.info(f"Réactions ajoutées au post {post._id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des réactions: {e}")
            return False
    
    def build_reactions_keyboard(
        self,
        post_id: str,
        reactions: List[str]
    ) -> InlineKeyboardMarkup:
        """
        Construit le clavier de réactions
        
        Args:
            post_id: ID du post
            reactions: Liste des réactions
        
        Returns:
            InlineKeyboardMarkup avec les boutons de réaction
        """
        keyboard = []
        row = []
        
        for i, reaction in enumerate(reactions):
            # Obtenir le compte
            count = self._get_reaction_count(post_id, reaction)
            
            # Créer le bouton
            button_text = f"{reaction} {count}" if count > 0 else reaction
            button = InlineKeyboardButton(
                text=button_text,
                callback_data=f"reaction:{post_id}:{reaction}"
            )
            row.append(button)
            
            # Nouvelle ligne tous les 3 boutons
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []
        
        # Ajouter la dernière ligne si nécessaire
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_reaction_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Gère le callback d'une réaction
        
        Args:
            update: Update Telegram
            context: Contexte
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Parser le callback data
            parts = query.data.split(":")
            if len(parts) != 3 or parts[0] != "reaction":
                return
            
            _, post_id, reaction = parts
            user_id = update.effective_user.id
            
            # Vérifier/Toggle la réaction de l'utilisateur
            toggled = await self._toggle_user_reaction(
                post_id,
                user_id,
                reaction
            )
            
            # Obtenir le post
            post = await self.posts_repo.get_post(post_id)
            if not post:
                return
            
            # Mettre à jour le clavier
            new_keyboard = self.build_reactions_keyboard(
                post_id,
                post.reactions
            )
            
            await query.edit_message_reply_markup(
                reply_markup=new_keyboard
            )
            
            # Feedback à l'utilisateur
            if toggled:
                await query.answer(f"Vous avez réagi avec {reaction}")
            else:
                await query.answer(f"Réaction {reaction} retirée")
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la réaction: {e}")
            await query.answer("Erreur lors du traitement de la réaction", show_alert=True)
    
    async def _toggle_user_reaction(
        self,
        post_id: str,
        user_id: int,
        reaction: str
    ) -> bool:
        """
        Active/désactive la réaction d'un utilisateur
        
        Args:
            post_id: ID du post
            user_id: ID de l'utilisateur
            reaction: Emoji de réaction
        
        Returns:
            True si ajouté, False si retiré
        """
        key = f"{post_id}:{reaction}"
        
        # Utiliser un set pour stocker les utilisateurs qui ont réagi
        if key not in self.reaction_counts:
            self.reaction_counts[key] = {"count": 0, "users": set()}
        
        users_set = self.reaction_counts[key]["users"]
        
        if user_id in users_set:
            # Retirer la réaction
            users_set.remove(user_id)
            self.reaction_counts[key]["count"] = len(users_set)
            
            # Mettre à jour en DB
            await self._update_reaction_count_db(post_id, reaction, -1)
            return False
        else:
            # Ajouter la réaction
            users_set.add(user_id)
            self.reaction_counts[key]["count"] = len(users_set)
            
            # Mettre à jour en DB
            await self._update_reaction_count_db(post_id, reaction, 1)
            return True
    
    async def _update_reaction_count_db(
        self,
        post_id: str,
        reaction: str,
        delta: int
    ):
        """
        Met à jour le compteur de réaction en DB
        
        Args:
            post_id: ID du post
            reaction: Emoji
            delta: Changement (+1 ou -1)
        """
        try:
            # Obtenir le post
            post = await self.posts_repo.get_post(post_id)
            if not post:
                return
            
            # Mettre à jour le compteur total
            new_count = max(0, post.reactions_count + delta)
            await self.posts_repo.update_post(
                post_id,
                {"reactions_count": new_count}
            )
            
            # On pourrait aussi stocker le détail par réaction dans metadata
            # Pour une implémentation complète
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du compteur: {e}")
    
    def _init_reaction_count(self, post_id: str, reaction: str):
        """
        Initialise le compteur pour une réaction
        
        Args:
            post_id: ID du post
            reaction: Emoji
        """
        key = f"{post_id}:{reaction}"
        if key not in self.reaction_counts:
            self.reaction_counts[key] = {"count": 0, "users": set()}
    
    def _get_reaction_count(self, post_id: str, reaction: str) -> int:
        """
        Obtient le nombre de réactions
        
        Args:
            post_id: ID du post
            reaction: Emoji
        
        Returns:
            Nombre de réactions
        """
        key = f"{post_id}:{reaction}"
        if key in self.reaction_counts:
            return self.reaction_counts[key]["count"]
        return 0
    
    def get_reaction_stats(self, post_id: str) -> dict:
        """
        Obtient les statistiques de réactions pour un post
        
        Args:
            post_id: ID du post
        
        Returns:
            Dict avec les stats par réaction
        """
        stats = {}
        
        for key, data in self.reaction_counts.items():
            if key.startswith(f"{post_id}:"):
                reaction = key.split(":")[1]
                stats[reaction] = {
                    "count": data["count"],
                    "users": list(data["users"])
                }
        
        return stats
