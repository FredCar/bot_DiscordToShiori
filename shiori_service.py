import os
import logging
import aiohttp
import time
import asyncio
from dotenv import load_dotenv

# Configuration du logging
logger = logging.getLogger('discord-shiori-bot')

# Charger les variables d'environnement
load_dotenv()

class ShioriService:
    def __init__(self):
        self.api_base_url = os.getenv('SHIORI_API_URL').rstrip('/')
        self.username = os.getenv('SHIORI_USERNAME')
        self.password = os.getenv('SHIORI_PASSWORD')
        self.token = None
        self.token_timestamp = 0
        self.token_expiry = 3600  # Durée de validité du token en secondes (par défaut 1h)
        
        # URL sans /api/v1 pour les endpoints d'API
        self.api_endpoint = self.api_base_url.replace('/api/v1', '')
        
        # Configuration des tentatives de reconnexion
        self.max_retries = 3
        self.retry_delay = 2  # secondes
        
    async def authenticate(self, force=False):
        """Authentification auprès de l'API Shiori."""
        # Vérifie si le token est encore valide (sauf si force=True)
        current_time = time.time()
        if not force and self.token and (current_time - self.token_timestamp) < self.token_expiry:
            return self.token
            
        auth_url = f"{self.api_base_url}/auth/login"
        logger.info(f"Tentative d'authentification à Shiori: {auth_url}")
        
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    resp = await session.post(
                        auth_url,
                        json={
                            "username": self.username,
                            "password": self.password,
                            "remember": True
                        },
                        timeout=30  # Timeout explicite
                    )
                    
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Extraire le token selon la structure de réponse
                        if 'session' in data:
                            self.token = data.get('session')
                        elif 'token' in data:
                            self.token = data.get('token')
                        elif isinstance(data, dict) and 'message' in data and 'token' in data['message']:
                            self.token = data['message']['token']
                        
                        self.token_timestamp = current_time
                        logger.info("Authentification réussie à Shiori")
                        return self.token
                    else:
                        body = await resp.text()
                        logger.warning(f"Échec d'authentification (tentative {retry_count+1}/{self.max_retries}): {resp.status} - {body[:200]}")
                        retry_count += 1
                        await asyncio.sleep(self.retry_delay)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout lors de l'authentification (tentative {retry_count+1}/{self.max_retries})")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
            except aiohttp.ClientError as e:
                logger.warning(f"Erreur réseau lors de l'authentification (tentative {retry_count+1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Erreur inattendue lors de l'authentification: {str(e)}")
                raise
                
        raise Exception(f"Échec d'authentification après {self.max_retries} tentatives")
    
    async def save_bookmark(self, url, description=""):
        """Enregistre une URL dans Shiori."""
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # S'assurer qu'on a un token valide
                await self.authenticate()
                
                # Préparation des données
                bookmark_data = {
                    "url": url,
                    "createArchive": True
                }
                
                if description:
                    bookmark_data["public"] = 0
                    bookmark_data["tags"] = []
                    bookmark_data["excerpt"] = description
                
                bookmark_url = f"{self.api_endpoint}/api/bookmarks"
                headers = {"Authorization": f"Bearer {self.token}"}
                
                logger.info(f"Tentative d'enregistrement d'URL: {url}")
                
                async with aiohttp.ClientSession() as session:
                    resp = await session.post(
                        bookmark_url,
                        json=bookmark_data,
                        headers=headers,
                        timeout=60  # Timeout plus long pour le téléchargement de la page
                    )
                    
                    status = resp.status
                    
                    # Si le token est invalide, on force une nouvelle authentification
                    if status in (401, 403):
                        logger.info("Token expiré, nouvelle authentification...")
                        await self.authenticate(force=True)
                        retry_count += 1
                        continue
                    
                    # Pour les erreurs 5xx, on retente
                    if 500 <= status < 600:
                        logger.warning(f"Erreur serveur {status}, nouvelle tentative {retry_count+1}/{self.max_retries}")
                        retry_count += 1
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    body = await resp.text()
                    
                    # Succès
                    if 200 <= status < 300:
                        logger.info(f"URL enregistrée dans Shiori avec succès: {url}")
                        return True
                    
                    # Autres erreurs
                    logger.error(f"Échec de l'enregistrement: {status} - {body[:200]}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout lors de l'enregistrement (tentative {retry_count+1}/{self.max_retries})")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
            except aiohttp.ClientError as e:
                logger.warning(f"Erreur réseau lors de l'enregistrement (tentative {retry_count+1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Erreur inattendue lors de l'enregistrement: {str(e)}")
                return False
                
        logger.error(f"Échec de l'enregistrement après {self.max_retries} tentatives: {url}")
        return False
