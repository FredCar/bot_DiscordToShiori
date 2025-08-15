#!/usr/bin/env python3
import os
import re
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import discord

# Importer le service Shiori existant
from shiori_service import ShioriService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('import-history')

# Charger les variables d'environnement
load_dotenv()

# ============================================================================ #
# CONFIGURATION - Modifiez ces variables pour exécuter depuis VSCode            #
# ============================================================================ #
# Nombre de jours dans le passé à récupérer (None = pas de limite de date)
DAYS = None
# Nombre maximum de messages à récupérer (None = pas de limite)
LIMIT = None  
# Nombre d'URLs à traiter par lot
BATCH_SIZE = 10  # Réduit à 10 pour éviter les problèmes de verrouillage de BDD
# Délai entre les requêtes individuelles (en secondes)
REQUEST_DELAY = 0.5  # Ajoute un délai entre chaque requête
# Délai entre les lots (en secondes)
BATCH_DELAY = 5  # Augmenté pour laisser la BDD se libérer entre les lots
# Inverser l'ordre d'importation (True = du plus ancien au plus récent)
REVERSE_ORDER = True
# Mode simulation (True = afficher les URLs sans les envoyer à Shiori)
DRY_RUN = False  
# Mode verbeux (True = afficher plus de détails)
VERBOSE = True  
# ============================================================================ #

# Configuration depuis .env
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

# Fonction pour extraire les URLs d'un texte
def extract_urls(text):
    """Extrait les URLs d'un texte."""
    if not text:
        return []
    
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)
    
    return urls

# Fonction principale pour récupérer et importer les messages
async def import_history(days=None, limit=None, batch_size=10, request_delay=0.5, batch_delay=5, 
                        reverse_order=False, dry_run=False):
    """Récupère et importe l'historique des messages."""
    if not all([DISCORD_TOKEN, DISCORD_CHANNEL_ID]):
        logger.error("Configuration incomplète. Vérifiez les variables d'environnement.")
        return

    # Initialiser le service Shiori si on n'est pas en mode simulation
    shiori_service = None
    if not dry_run:
        shiori_service = ShioriService()
        try:
            # Tester l'authentification
            logger.info("Test de connexion à Shiori...")
            token = await shiori_service.authenticate()
            if not token:
                logger.error("Impossible de s'authentifier auprès de Shiori. Import annulé.")
                logger.info("Utilisez --dry-run pour récupérer les URLs sans tenter de les envoyer à Shiori.")
                return
            logger.info("Connexion à Shiori établie avec succès!")
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Shiori: {e}")
            logger.info("Utilisez --dry-run pour récupérer les URLs sans tenter de les envoyer à Shiori.")
            return
    
    # Configurer le client Discord
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    # Variables pour stocker les résultats
    messages_with_urls = []
    
    @client.event
    async def on_ready():
        logger.info(f"{client.user} est connecté à Discord!")
        
        try:
            # Récupérer le canal
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            if not channel:
                logger.error(f"Canal avec ID {DISCORD_CHANNEL_ID} non trouvé!")
                await client.close()
                return
            
            logger.info(f"Récupération des messages du canal #{channel.name} dans {channel.guild.name}")
            
            # Définir la date limite si spécifiée
            after = None
            if days:
                after = datetime.now() - timedelta(days=days)
                logger.info(f"Récupération des messages après {after.strftime('%Y-%m-%d')}")
            
            # Compteurs
            processed_count = 0
            urls_found = 0
            
            # Récupérer les messages
            # Par défaut, les messages sont récupérés du plus récent au plus ancien
            messages_history = []
            async for message in channel.history(limit=limit, after=after, oldest_first=False):
                processed_count += 1
                
                if message.author != client.user:  # Ignorer les messages du bot
                    urls = extract_urls(message.content)
                    
                    if urls:
                        urls_found += len(urls)
                        for url in urls:
                            messages_history.append({
                                'message_id': message.id,
                                'author': str(message.author),
                                'content': message.content,
                                'timestamp': message.created_at,
                                'url': url
                            })
                
                if processed_count % 100 == 0:
                    logger.info(f"Progression: {processed_count} messages traités, {urls_found} URLs trouvées")
            
            logger.info(f"Récupération terminée. {processed_count} messages traités, {len(messages_history)} messages avec URLs trouvés.")
            
            # Inverser l'ordre des messages si demandé (pour les traiter du plus ancien au plus récent)
            if reverse_order:
                logger.info("Inversion de l'ordre des messages (traitement du plus ancien au plus récent)...")
                messages_history.sort(key=lambda x: x['timestamp'])
                messages_with_urls = messages_history
            else:
                messages_with_urls = messages_history
            
            # Si mode simulation, afficher seulement les informations
            if dry_run:
                logger.info("Mode simulation activé. Aucune URL ne sera envoyée à Shiori.")
                for msg in messages_with_urls:
                    logger.info(f"URL: {msg['url']}")
                    logger.info(f"  Message: {msg['content'][:50]}...")
                    logger.info(f"  Auteur: {msg['author']}")
                    logger.info(f"  Date: {msg['timestamp']}")
                    logger.info("---")
            else:
                # Importer les URLs dans Shiori
                total_urls = len(messages_with_urls)
                success_count = 0
                fail_count = 0
                
                logger.info(f"Début de l'importation de {total_urls} URLs vers Shiori...")
                
                # Traiter par lots
                for i in range(0, total_urls, batch_size):
                    batch = messages_with_urls[i:i+batch_size]
                    logger.info(f"Traitement du lot {i//batch_size + 1}/{(total_urls-1)//batch_size + 1} ({len(batch)} URLs)")
                    
                    for msg in batch:
                        result = await shiori_service.save_bookmark(msg['url'], msg['content'])
                        if result:
                            success_count += 1
                        else:
                            fail_count += 1
                        
                        # Délai entre chaque requête pour éviter le verrouillage de la base de données
                        await asyncio.sleep(request_delay)
                    
                    # Pause plus longue entre les lots pour permettre à SQLite de libérer les verrous
                    if i + batch_size < total_urls:
                        logger.info(f"Pause de {batch_delay} secondes entre les lots pour éviter le verrouillage de la base de données...")
                        await asyncio.sleep(batch_delay)
                
                logger.info(f"Importation terminée. {success_count} URLs importées avec succès, {fail_count} échecs.")
            
            await client.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution: {e}", exc_info=True)
            await client.close()
    
    # Fermer proprement les connexions pour éviter l'erreur "Unclosed connector"
    await asyncio.sleep(1)  # Attendre que toutes les opérations async se terminent
    
    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à Discord: {e}", exc_info=True)
    finally:
        # S'assurer que le client Discord est correctement fermé
        if not client.is_closed():
            await client.close()

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description="Importer l'historique des messages Discord vers Shiori")
    parser.add_argument("-d", "--days", type=int, help="Nombre de jours dans le passé à partir duquel récupérer les messages")
    parser.add_argument("-l", "--limit", type=int, help="Nombre maximum de messages à récupérer")
    parser.add_argument("-b", "--batch-size", type=int, default=10, help="Nombre d'URLs à traiter par lot (défaut: 10)")
    parser.add_argument("-r", "--request-delay", type=float, default=0.5, help="Délai entre chaque requête en secondes (défaut: 0.5)")
    parser.add_argument("-bd", "--batch-delay", type=float, default=5, help="Délai entre les lots en secondes (défaut: 5)")
    parser.add_argument("--reverse", action="store_true", help="Inverser l'ordre d'importation (du plus ancien au plus récent)")
    parser.add_argument("--dry-run", action="store_true", help="Mode simulation: afficher les URLs sans les envoyer à Shiori")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux: afficher plus de détails")
    
    args = parser.parse_args()
    
    # Vérifier si les arguments ont été spécifiés, pas leurs valeurs
    # argparse définit les arguments non spécifiés avec leurs valeurs par défaut
    # Pour vérifier si un argument a été explicitement fourni, nous devons le comparer avec None
    # ou utiliser une approche différente
    
    # Ces vérifications utilisent des valeurs par défaut personnalisées si l'argument n'est pas spécifié
    days = args.days if args.days is not None else DAYS
    limit = args.limit if args.limit is not None else LIMIT
    reverse_order = args.reverse or REVERSE_ORDER
    dry_run = args.dry_run or DRY_RUN
    verbose = args.verbose or VERBOSE
    
    # Pour ces paramètres, nous devrions aussi vérifier si l'argument a été fourni
    # et non pas comparer avec une valeur spécifique
    batch_size = BATCH_SIZE
    if hasattr(args, 'batch_size') and args.batch_size is not None:
        batch_size = args.batch_size
        
    request_delay = REQUEST_DELAY
    if hasattr(args, 'request_delay') and args.request_delay is not None:
        request_delay = args.request_delay
        
    batch_delay = BATCH_DELAY
    if hasattr(args, 'batch_delay') and args.batch_delay is not None:
        batch_delay = args.batch_delay
    
    # Configuration du niveau de logging
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        asyncio.run(import_history(days=days, limit=limit, batch_size=batch_size, 
                                  request_delay=request_delay, batch_delay=batch_delay,
                                  reverse_order=reverse_order, dry_run=dry_run))
    except KeyboardInterrupt:
        logger.info("Opération interrompue par l'utilisateur.")
    except Exception as e:
        logger.error(f"Erreur lors de l'importation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()