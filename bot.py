import os
import re
import logging
import discord
from dotenv import load_dotenv
from shiori_service import ShioriService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord-shiori-bot')

# Charger les variables d'environnement
load_dotenv()

# Configuration
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))  # Par défaut 0 si non défini

# Configurer les intentions Discord
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour lire le contenu des messages

# Initialiser le client Discord
client = discord.Client(intents=intents)
shiori_service = ShioriService()

@client.event
async def on_ready():
    """Événement déclenché lorsque le bot est prêt."""
    logger.info(f"{client.user} est connecté à Discord!")

    # Vérifier l'existence du canal
    if CHANNEL_ID:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            logger.info(f"Canal surveillé: #{channel.name} dans {channel.guild.name}")
        else:
            logger.error(f"ERREUR: Canal avec ID {CHANNEL_ID} non trouvé!")
    else:
        logger.error("Aucun ID de canal spécifié. Veuillez configurer le fichier .env.")

@client.event
async def on_message(message):
    """Événement déclenché à chaque message."""
    # Ignorer les messages du bot lui-même
    if message.author == client.user:
        return

    # Vérifier si le message est dans le canal surveillé
    if message.channel.id == CHANNEL_ID:
        logger.info(f"Message dans le canal surveillé: '{message.content}'")

        # Extraire les URLs du message
        url_pattern = r'(https?://[^\s]+)'
        urls = re.findall(url_pattern, message.content)

        if urls:
            logger.info(f"URLs trouvées: {len(urls)}")
            for url in urls:
                logger.info(f"URL détectée: {url}")
                try:
                    result = await shiori_service.save_bookmark(url, message.content)
                    if not result:
                        logger.warning(f"L'URL n'a pas pu être enregistrée dans Shiori: {url}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'enregistrement de l'URL: {e}", exc_info=True)
        else:
            logger.info("Aucune URL trouvée dans le message")

# Lancer le bot
if __name__ == "__main__":
    try:
        logger.info("Démarrage du bot...")
        client.run(TOKEN)
    except discord.errors.LoginFailure as e:
        logger.error(f"Erreur d'authentification Discord: {e}")
        logger.error("Vérifiez votre token Discord dans le fichier .env")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}", exc_info=True)
        logger.error("Si vous venez de créer le bot, assurez-vous qu'il est invité dans au moins un serveur.")