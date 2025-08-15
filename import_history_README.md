# Script d'importation de l'historique Discord vers Shiori

Ce script permet d'importer l'historique des liens postés dans un canal Discord spécifique vers Shiori, un gestionnaire de bookmarks. Il est conçu pour être exécuté ponctuellement, contrairement au bot principal qui surveille en continu.

## Prérequis

- Python 3.8 ou supérieur
- Les mêmes dépendances que le bot principal (discord.py, requests, python-dotenv)
- Un fichier `.env` correctement configuré avec les variables d'environnement nécessaires

## Configuration

Le script utilise le même fichier `.env` que le bot principal. Assurez-vous que les variables suivantes sont configurées:

```properties
DISCORD_TOKEN=votre_token_discord
DISCORD_CHANNEL_ID=id_du_canal_à_importer
SHIORI_API_URL=url_api_shiori
SHIORI_USERNAME=utilisateur_shiori
SHIORI_PASSWORD=mot_de_passe_shiori
```

## Utilisation

```bash
python import_history.py [options]
```

### Options disponibles

- `-d`, `--days` : Nombre de jours dans le passé à partir duquel récupérer les messages
- `-l`, `--limit` : Nombre maximum de messages à récupérer
- `-b`, `--batch-size` : Nombre d'URLs à traiter par lot (défaut: 10)
- `-r`, `--request-delay` : Délai entre chaque requête en secondes (défaut: 0.5)
- `-bd`, `--batch-delay` : Délai entre les lots en secondes (défaut: 5)
- `--reverse` : Inverser l'ordre d'importation (du plus ancien au plus récent)
- `--dry-run` : Mode simulation - affiche les URLs sans les envoyer à Shiori
- `-v`, `--verbose` : Mode verbeux - affiche plus de détails

### Exemples d'utilisation

1. **Importer tous les liens** (peut prendre du temps sur les grands canaux):
   ```bash
   python import_history.py
   ```

2. **Importer les liens des 7 derniers jours**:
   ```bash
   python import_history.py --days 7
   ```

3. **Limiter le nombre de messages à analyser**:
   ```bash
   python import_history.py --limit 1000
   ```

4. **Tester sans envoyer à Shiori** (utile pour vérifier quels liens seront importés):
   ```bash
   python import_history.py --days 7 --dry-run
   ```

5. **Ajuster les délais pour éviter les erreurs de base de données**:
   ```bash
   python import_history.py --batch-size 5 --request-delay 1 --batch-delay 10
   ```

6. **Importer dans l'ordre chronologique** (du plus ancien au plus récent):
   ```bash
   python import_history.py --reverse
   ```

## Résolution des problèmes

### Erreur "database is locked" (SQLite_BUSY)

Cette erreur se produit lorsque Shiori ne peut pas accéder à sa base de données SQLite car elle est verrouillée par une autre opération. Pour résoudre ce problème:

1. Réduisez la taille des lots (`--batch-size`)
2. Augmentez les délais entre les requêtes (`--request-delay`) et entre les lots (`--batch-delay`)
3. Assurez-vous qu'aucune autre opération lourde n'est en cours sur Shiori

### Erreur de connexion à Discord ou Shiori

1. Vérifiez que vos tokens et identifiants dans le fichier `.env` sont corrects
2. Assurez-vous que le bot Discord a accès au canal spécifié
3. Vérifiez que Shiori est accessible et en cours d'exécution

### Le script prend trop de temps

Pour les grands canaux avec beaucoup de messages, le script peut prendre du temps. Vous pouvez:
- Limiter le nombre de jours (`--days`) ou le nombre de messages (`--limit`)
- Exécuter le script pendant les périodes de faible utilisation
- Augmenter la taille des lots (`--batch-size`) si votre serveur Shiori le permet

## Remarque importante

Ce script est conçu pour une utilisation ponctuelle et peut imposer une charge importante sur vos serveurs Discord et Shiori. Utilisez-le avec précaution, de préférence pendant les périodes de faible activité.
