#!/usr/bin/env python
"""
Script de lancement du bot
"""

import sys
import os

# Ajouter le dossier bot au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Lancer le bot
if __name__ == "__main__":
    from bot.main import main
    main()
