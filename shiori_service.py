import os
import logging
import aiohttp
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
        
        # URL sans /api/v1 pour les endpoints d'API
        self.api_endpoint = self.api_base_url.replace('/api/v1', '')
        
    async def authenticate(self):
        """Authentification auprès de l'API Shiori."""
        auth_url = f"{self.api_base_url}/auth/login"
        
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    auth_url,
                    json={
                        "username": self.username,
                        "password": self.password,
                        "remember": True
                    }
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
                    
                    logger.info("Authentification réussie à Shiori")
                    return self.token
                else:
                    body = await resp.text()
                    raise Exception(f"Échec d'authentification: {resp.status} - {body}")
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Shiori: {str(e)}")
            raise
    
    async def save_bookmark(self, url, description=""):
        """Enregistre une URL dans Shiori."""
        try:
            # S'assurer qu'on a un token
            if not self.token:
                await self.authenticate()
            
            # Préparation des données - simplifié pour minimiser les erreurs
            # Utilisons seulement les champs essentiels selon la documentation
            bookmark_data = {
                "url": url
            }
            
            # Seulement ajouter ces champs s'ils sont vraiment nécessaires
            # bookmark_data["createArchive"] = True
            # bookmark_data["public"] = 0
            
            bookmark_url = f"{self.api_endpoint}/api/bookmarks"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    bookmark_url,
                    json=bookmark_data,
                    headers=headers
                )
                
                status = resp.status
                body = await resp.text()
                logger.info(f"Réponse: statut={status}, corps={body[:100]}...")
                
                # Session expirée
                if status in (401, 403, 500):
                    logger.info("Session expirée, tentative de reconnexion...")
                    await self.authenticate()
                    
                    # Essayons avec seulement le token dans l'URL comme paramètre
                    # C'est une méthode alternative qui peut fonctionner avec certaines versions de Shiori
                    retry_url = f"{bookmark_url}?token={self.token}"
                    retry_resp = await session.post(
                        retry_url,
                        json=bookmark_data
                        # Pas d'en-tête Authorization ici
                    )
                    
                    retry_status = retry_resp.status
                    retry_body = await retry_resp.text()
                    logger.info(f"Réponse après reconnexion: statut={retry_status}, corps={retry_body[:100]}...")
                    
                    if 200 <= retry_status < 300:
                        logger.info(f"URL enregistrée dans Shiori: {url}")
                        return True
                    else:
                        # Si cela échoue aussi, essayons une dernière approche
                        alt_headers = {"X-Session-Id": self.token}  # Format alternatif d'authentification
                        last_resp = await session.post(
                            bookmark_url,
                            json=bookmark_data,
                            headers=alt_headers
                        )
                        
                        last_status = last_resp.status
                        last_body = await last_resp.text()
                        logger.info(f"Dernière tentative: statut={last_status}, corps={last_body[:100]}...")
                        
                        if 200 <= last_status < 300:
                            logger.info(f"URL enregistrée dans Shiori avec X-Session-Id: {url}")
                            return True
                        else:
                            raise Exception(f"Échec de l'enregistrement: {retry_status} - {retry_body[:100]}")
                
                # Succès
                if 200 <= status < 300:
                    logger.info(f"URL enregistrée dans Shiori: {url}")
                    return True
                
                # Erreur
                raise Exception(f"Échec de l'enregistrement: {status} - {body[:100]}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement dans Shiori: {str(e)}")
            raise
