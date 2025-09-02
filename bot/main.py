"""
Bot Telegram principal - Point d'entrée de l'application
"""

import asyncio
import logging
from telegram.ext import Application

from bot.config import Config
from bot.logger import setup_logger
from bot.handlers.dispatcher import register_handlers
from bot.db.motor_client import MongoClient
from bot.schedule.scheduler import JobScheduler

# Setup logging
logger = setup_logger(__name__)


class TelegramBot:
    """Classe principale du bot Telegram"""
    
    def __init__(self):
        self.config = Config()
        self.app = None
        self.db = None
        self.scheduler = None
        
    async def initialize(self):
        """Initialise les composants du bot"""
        try:
            # Connexion à la base de données (DESACTIVE TEMPORAIREMENT)
            # self.db = MongoClient(self.config.MONGO_URI)
            # await self.db.connect()
            logger.info("⚠️ Mode test : MongoDB désactivé temporairement")
            
            # Création de l'application PTB
            self.app = (
                Application.builder()
                .token(self.config.BOT_TOKEN)
                .build()
            )
            
            # Enregistrement des handlers
            register_handlers(self.app)
            logger.info("✅ Handlers enregistrés")
            
            # Initialisation du scheduler (DESACTIVE)
            # self.scheduler = JobScheduler(self.db)
            # await self.scheduler.start()
            # await self.scheduler.restore_jobs()
            logger.info("⚠️ Scheduler désactivé en mode test")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
            
    async def run(self):
        """Lance le bot"""
        try:
            await self.initialize()
            
            # Démarrage du bot
            await self.app.initialize()
            await self.app.start()
            logger.info("🤖 Bot démarré avec succès!")
            
            # Polling
            await self.app.updater.start_polling(
                drop_pending_updates=True
            )
            
            # Garder le bot en vie
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏸️ Arrêt du bot...")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Arrêt propre du bot"""
        try:
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                
            # if self.scheduler:
            #     await self.scheduler.shutdown()
                
            # if self.db:
            #     await self.db.disconnect()
                
            logger.info("👋 Bot arrêté proprement")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt: {e}")


def main():
    """Point d'entrée principal"""
    bot = TelegramBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
