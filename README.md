# 🤖 Bot Telegram de Publication

Bot Telegram modulaire pour la gestion et la publication de contenu dans les canaux.

## ✨ Fonctionnalités

- 📢 **Gestion multi-canaux** - Publiez dans plusieurs canaux simultanément
- ⏰ **Planification** - Programmez vos publications à l'avance
- 📁 **Renommage de fichiers** - Renommez et réuploadez des fichiers
- 🖼️ **Gestion des thumbnails** - Ajoutez des miniatures personnalisées
- 👍 **Réactions** - Ajoutez des réactions style "like bot"
- 🔗 **Boutons URL** - Ajoutez des boutons personnalisés
- 🗑️ **Auto-suppression** - Suppression automatique après X heures
- 🔒 **Force Subscribe** - Obligation de rejoindre un canal
- ⚡ **Rate Limiting** - Protection contre le spam

## 📁 Structure du Projet

```
bot/
├── main.py                 # Point d'entrée
├── config.py              # Configuration centralisée
├── logger.py              # Système de logging
│
├── clients/               # Clients Telegram
│   ├── ptb_app.py        # Python-Telegram-Bot
│   ├── telethon_client.py
│   └── pyrogram_client.py
│
├── db/                    # Base de données
│   ├── motor_client.py   # Client MongoDB
│   ├── indexes.py        # Index MongoDB
│   └── repositories/     # Pattern Repository
│       ├── users_repo.py
│       ├── channels_repo.py
│       ├── posts_repo.py
│       ├── schedules_repo.py
│       ├── files_repo.py
│       └── settings_repo.py
│
├── models/               # Modèles de données
│   ├── user.py
│   ├── channel.py
│   ├── post.py
│   ├── schedule.py
│   ├── settings.py
│   └── file.py
│
├── utils/                # Utilitaires
│   ├── constants.py
│   ├── errors.py
│   ├── validators.py
│   ├── timezone.py
│   ├── fileops.py
│   ├── throttling.py
│   ├── forcesub.py
│   └── queues.py
│
├── publications/         # Gestion des publications
│   ├── receive_post.py
│   ├── send_post.py
│   ├── add_reactions.py
│   └── add_url_buttons.py
│
├── rename_file/          # Renommage de fichiers
│   ├── save_thumbnail.py
│   └── rename_file.py
│
├── schedule/             # Planification
│   ├── scheduler.py
│   └── autodelete.py
│
└── handlers/             # Handlers Telegram
    ├── start.py
    └── dispatcher.py
```

## 🚀 Installation

### Prérequis

- Python 3.10+
- MongoDB
- Bot Telegram (créé via @BotFather)

### Étapes

1. **Cloner le projet**
```bash
git clone https://github.com/votre-repo/telegram-bot.git
cd telegram-bot
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

4. **Base de données**
```bash
# Démarrer MongoDB
mongod

# Ou avec Docker
docker run -d -p 27017:27017 --name mongodb mongo
```

5. **Lancer le bot**
```bash
python bot/main.py
```

## ⚙️ Configuration

Créez un fichier `.env` à la racine du projet :

```env
# Bot
BOT_TOKEN=votre_token_ici
BOT_USERNAME=votre_bot

# Database
MONGO_URI=mongodb://localhost:27017
DB_NAME=telegram_bot

# Admins
ADMIN_IDS=123456789
OWNER_ID=123456789

# Options
ENABLE_REACTIONS=true
ENABLE_SCHEDULER=true
DEFAULT_TIMEZONE=Europe/Paris
```

## 📝 Utilisation

### Commandes principales

- `/start` - Démarrer le bot
- `/help` - Afficher l'aide
- `/channels` - Gérer vos canaux
- `/post` - Créer un nouveau post
- `/schedule` - Planifier une publication
- `/settings` - Paramètres

### Workflow typique

1. **Ajouter un canal** : `/channels` → "Ajouter"
2. **Créer un post** : Envoyez du contenu (texte, photo, vidéo...)
3. **Sélectionner les canaux** : Choisissez où publier
4. **Planifier ou envoyer** : Immédiat ou programmé
5. **Ajouter des options** : Réactions, boutons, auto-delete

## 🔧 Architecture

### Pattern Repository

Le projet utilise le pattern Repository pour séparer la logique métier de l'accès aux données :

- **Models** : Définissent la structure des données
- **Repositories** : Gèrent les opérations CRUD
- **Services** : Contiennent la logique métier

### Gestion asynchrone

- Utilisation d'`asyncio` pour les opérations asynchrones
- `Motor` pour MongoDB asynchrone
- `APScheduler` pour les tâches planifiées

### Modularité

Chaque fonctionnalité est isolée dans son module :
- Facilite la maintenance
- Permet l'ajout/suppression de fonctionnalités
- Tests unitaires simplifiés

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Motor](https://motor.readthedocs.io/)
- [APScheduler](https://apscheduler.readthedocs.io/)

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Contactez via Telegram : @votre_username

---

Fait avec ❤️ pour la communauté Telegram
