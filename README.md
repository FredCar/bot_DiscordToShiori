# Bot Discord-Shiori

Un bot Discord qui envoie automatiquement les liens postés dans un canal spécifique vers Shiori, un gestionnaire de bookmarks.

## Installation

1. Créer l'environnement virtuel Python :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou venv\Scripts\activate  # Sur Windows
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurer les variables d'environnement dans le fichier `.env` :
   - `DISCORD_TOKEN` : Token de votre bot Discord.
   - `SHIORI_API_URL` : URL de l'API Shiori (ex : http://localhost:8080/api/v1).
   - `SHIORI_USERNAME` : Nom d'utilisateur Shiori.
   - `SHIORI_PASSWORD` : Mot de passe Shiori.
   - `DISCORD_CHANNEL_ID` : ID du canal Discord à surveiller.

   Exemple de fichier `.env` :
   ```properties
   DISCORD_TOKEN=VotreTokenDiscordIci
   SHIORI_API_URL=http://localhost:8080/api/v1
   SHIORI_USERNAME=VotreNomUtilisateur
   SHIORI_PASSWORD=VotreMotDePasse
   DISCORD_CHANNEL_ID=123456789012345678
   ```

## Utilisation

1. Démarrer le bot :
   ```bash
   python bot.py
   ```

2. Le bot surveillera le canal spécifié (défini par `DISCORD_CHANNEL_ID`) et enverra automatiquement les liens postés vers Shiori.

---

## Déploiement avec Docker

### Étape 1 : Construire l'image Docker sur le NAS via SSH
1. Connectez-vous à votre NAS via SSH :
   ```bash
   ssh <votre_utilisateur>@<adresse_IP_du_NAS>
   ```

2. Naviguez vers le dossier contenant le projet :
   ```bash
   cd /mnt/volume1/app_data/Bot_Discord-Shiori
   ```

3. Construisez l'image Docker :
   ```bash
   docker build -t discord-bot .
   ```

4. Vérifiez que l'image a été créée :
   ```bash
   docker images
   ```
   Vous devriez voir une ligne avec le nom `discord-bot`.

---

### Étape 2 : Déployer avec Portainer
1. **Accédez à Portainer** :
   - Connectez-vous à l'interface web de Portainer via votre navigateur.

2. **Créer un nouveau conteneur** :
   - Allez dans **Containers** > **Add Container**.
   - **Nom du conteneur** : `discord-bot`.
   - **Image** : Entrez le nom de l'image que vous avez construite, par exemple `discord-bot:latest`.

3. **Configurer les variables d'environnement** :
   - Cliquez sur **Advanced container settings** > **Env**.
   - Ajoutez les variables suivantes :
     - `DISCORD_TOKEN` : Votre token Discord.
     - `SHIORI_API_URL` : URL de l'API Shiori.
     - `SHIORI_USERNAME` : Nom d'utilisateur Shiori.
     - `SHIORI_PASSWORD` : Mot de passe Shiori.
     - `DISCORD_CHANNEL_ID` : ID du canal Discord à surveiller.

4. **Configurer la politique de redémarrage** :
   - Dans **Advanced container settings** > **Restart Policy**, sélectionnez `Always` pour que le conteneur redémarre automatiquement en cas de crash ou de redémarrage du NAS.

5. **Lancer le conteneur** :
   - Cliquez sur **Deploy the container** pour démarrer le bot.

---

## Fonctionnalités

- **Détection automatique des URLs** : Le bot détecte les liens dans les messages postés dans le canal surveillé.
- **Enregistrement des URLs dans Shiori** : Les liens détectés sont envoyés à Shiori avec le contenu du message comme description.
- **Gestion des erreurs** : Le bot gère les erreurs réseau et les problèmes d'authentification avec des messages de log détaillés.
- **Reconnexion automatique** : Le bot se reconnecte automatiquement en cas de déconnexion.

## Tests

Pour exécuter les tests unitaires, utilisez la commande suivante :
```bash
python -m unittest discover
```

## Dépendances

- `discord.py` : Pour interagir avec l'API Discord.
- `requests` : Pour les appels HTTP vers l'API Shiori.
- `python-dotenv` : Pour charger les variables d'environnement depuis un fichier `.env`.

## Notes importantes

- **Permissions Discord** : Assurez-vous que le bot a les permissions nécessaires pour lire les messages dans le canal spécifié.
- **Configuration Shiori** : Vérifiez que l'API Shiori est accessible et que les identifiants fournis dans le fichier `.env` sont corrects.
- **Canal Discord** : Le bot surveille uniquement le canal spécifié par `DISCORD_CHANNEL_ID`. Si l'ID est incorrect ou si le bot n'a pas accès au canal, il ne fonctionnera pas correctement.

## Exemple de flux

1. Un utilisateur poste un message contenant une URL dans le canal surveillé.
2. Le bot détecte l'URL et l'envoie à Shiori avec le contenu du message comme description.
3. Shiori enregistre le lien comme un nouveau signet.

## Support

Pour toute question ou problème, veuillez ouvrir une issue dans ce dépôt.