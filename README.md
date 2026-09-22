# RAG Enterprise Lab

Blueprint technique d'un RAG d'entreprise gouverné pour **GenAI Enterprise Lab**.

## Objectif
> Retrouver la bonne information, dans la bonne version, pour la bonne personne, avec des sources vérifiables.

Cas simulé :
- 120 collaborateurs
- 5 000 ressources documentaires à terme
- contrats clients / prestataires / RH
- conventions, grilles tarifaires, procédures, runbooks
- complétude documentaire
- conflits de versions
- ACL / RBAC / ABAC
- RGPD
- audit et évaluation
- cas métier phare : clôture mensuelle des signatures commerciales

## Architecture cloud-first
Le poste de développement ne doit pas contenir le corpus complet.

- Cloudflare R2 EU : documents originaux et dérivés
- Docling Worker : parsing/OCR/structure, exécuté à distance
- PostgreSQL + pgvector : registre documentaire, métadonnées, chunks, embeddings
- Jev adapter : décisions typées / scoring / routing (jamais pour l'autorisation)
- Claude : raisonnement et génération de réponse sourcée
- Identity Provider : Entra ID cible ; mock claims en DEV
- Apache / reverse proxy : couche HTTP / routes protégées
- GitHub : code, schémas, scripts, tests — jamais les 5 000 documents

## Phase 0
Cette archive contient uniquement le socle. Aucune donnée volumineuse n'est incluse.

## Démarrage
1. Dézipper par exemple dans `C:\RAG-Enterprise-Lab`.
2. Copier `.env.example` vers `.env`.
3. Ne renseigner aucun secret dans Git.
4. Ouvrir le dossier avec Claude Code.
5. Lui donner : **"Lis CLAUDE.md et exécute uniquement la Phase 0."**

## Règles non négociables
1. Never trust the LLM for authorization.
2. ACL/RBAC/ABAC sont évalués avant que le contenu ne soit transmis au LLM.
3. Une information interdite ne doit jamais entrer dans le contexte Claude.
4. Une version plus récente n'est pas forcément la version juridiquement applicable.
5. Toute réponse métier factuelle doit être traçable jusqu'à une source.
6. Les données volumineuses restent cloud.
