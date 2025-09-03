"""
Bot Telegram principal - Point d'entrée de l'application
"""
import logging
from telegram.ext import Application

from bot.config import Config
from bot.logger import setup_logger
from bot.handlers.dispatcher import register_handlers

logger = setup_logger(__name__)

def main():
    """Point d'entrée principal"""
    try:
        # Configuration
        config = Config()
        
        # Mode test : DB & scheduler désactivés
        logger.info("Mode test : MongoDB desactive temporairement")
        logger.info("Scheduler desactive en mode test")
        
        # Création de l'application PTB
        app = (
            Application.builder()
            .token(config.BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )
        
        # Enregistrer les handlers
        register_handlers(app)
        logger.info("Handlers enregistres")
        
        # Lancer le bot
        logger.info("Demarrage du bot...")
        app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        logger.info("Arret du bot...")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise

if __name__ == "__main__":
    main()