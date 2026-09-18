# SalesBoard

Tableau de bord Django pour saisir, importer et analyser des ventes. Chaque utilisateur consulte ses propres données ; les membres de l’équipe disposant du statut `staff` peuvent consulter l’ensemble des ventes.

## Fonctionnalités

- authentification Django et isolation des données par utilisateur ;
- saisie manuelle avec calcul automatique du total ;
- import CSV UTF-8 transactionnel (aucune écriture partielle) ;
- indicateurs de chiffre d’affaires, transactions, quantités et produits ;
- graphique journalier filtrable par période ;
- interface responsive en français ;
- configuration locale SQLite et production PostgreSQL ;
- tests automatisés et CI GitHub Actions.

## Installation locale

Prérequis : Python 3.12.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrez `http://127.0.0.1:8000/`. SQLite est utilisé localement lorsqu’aucune variable `DATABASE_URL` n’est définie.

## Docker

Prérequis : Docker Desktop ou Docker Engine avec Compose.

```bash
docker compose up --build
```

L’application est disponible sur `http://127.0.0.1:8000/`. Le service `web` attend que PostgreSQL soit prêt, applique automatiquement les migrations puis démarre Gunicorn. Les données PostgreSQL sont conservées dans le volume nommé `salesboard_postgres_data`.

Créez ensuite un administrateur dans un second terminal :

```bash
docker compose exec web python manage.py createsuperuser
```

Pour personnaliser les identifiants, le port ou les hôtes autorisés :

```bash
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

Arrêt simple : `docker compose down`. Pour supprimer également la base locale Docker : `docker compose down --volumes` (cette dernière commande efface les données du volume).

## Format CSV

Le fichier doit être encodé en UTF-8 et séparé par des points-virgules :

```csv
Product;Price;Quantity;Date
Clavier;49.90;2;2026-09-18 10:30
Écran;249.00;1;2026-09-18
```

Les colonnes obligatoires sont `Product`, `Price`, `Quantity` et `Date`. Une éventuelle colonne `Seller` est ignorée : les ventes importées appartiennent toujours au compte connecté.

## Déploiement sur Vercel

Le dépôt contient un point d’entrée WSGI explicite dans `api/index.py` et un `vercel.json`. Cette configuration reste compatible avec les projets Vercel anciens qui ne déclenchent pas encore la détection Django automatique.

1. Poussez le dépôt sur GitHub et importez-le dans Vercel.
2. Ajoutez une base PostgreSQL persistante depuis le Marketplace Vercel (Neon, Supabase, etc.). N’utilisez pas SQLite en production : le système de fichiers des fonctions serverless n’est pas une base persistante.
3. Configurez les variables d’environnement suivantes dans Vercel :

   - `DATABASE_URL` : URL de connexion PostgreSQL fournie par le service ;
   - `DJANGO_SECRET_KEY` : longue valeur aléatoire et secrète ;
   - `DJANGO_DEBUG=False` ;
   - `DJANGO_ALLOWED_HOSTS=.vercel.app,votre-domaine.fr` ;
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://votre-domaine.fr`.

4. Appliquez les migrations à la base de production depuis votre machine après avoir récupéré les variables Vercel :

```bash
vercel link
vercel env pull .env.production.local
# Chargez DATABASE_URL depuis ce fichier dans votre terminal, puis :
python manage.py migrate
python manage.py createsuperuser
```

Ne commitez jamais le fichier de variables téléchargé. Redéployez ensuite le projet si nécessaire.

`DATABASE_URL` doit impérativement pointer vers PostgreSQL en production. Sans elle, SQLite serait éphémère dans une fonction serverless et les tables ne seraient pas persistantes.

## Déploiement sur Render

Le fichier [`render.yaml`](render.yaml) décrit un service web Docker gratuit dans la région de Francfort. Render construit le `Dockerfile`, injecte son port dans `PORT`, vérifie `/login/` et redéploie automatiquement les nouveaux commits.

1. Dans Render, créez un nouveau **Blueprint** depuis ce dépôt GitHub.
2. Lorsque Render le demande, renseignez `DATABASE_URL` avec l’URL PostgreSQL mutualisée de production et `DATABASE_URL_UNPOOLED` avec l’URL directe réservée aux migrations. Ne placez jamais ces URL directement dans `render.yaml`.
3. Render génère automatiquement `DJANGO_SECRET_KEY`, construit l’image et applique les migrations au démarrage.

L’offre gratuite peut mettre le service en veille après une période sans trafic ; la première requête suivante peut donc être plus lente.

## Important avant de rendre le dépôt public

Les premiers commits de ce projet contenaient `db.sqlite3` et une ancienne clé Django de développement. Les supprimer du dernier commit ne les efface pas de l’historique Git. Avant de publier **cet historique existant**, créez de préférence un nouveau dépôt à partir de l’état actuel (un seul commit propre), ou nettoyez l’historique avec `git filter-repo`. Changez aussi le mot de passe de tout compte qui existait dans l’ancienne base.

## Vérifications avant publication

```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

## Variables d’environnement

Consultez [`.env.example`](.env.example). En production, l’application refuse de démarrer avec la clé de développement par défaut lorsque `DJANGO_DEBUG=False`.
