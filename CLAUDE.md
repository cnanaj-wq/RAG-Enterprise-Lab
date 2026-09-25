# CLAUDE.md — RAG Enterprise Lab

Tu travailles sur **RAG Enterprise Lab**, un laboratoire réaliste de RAG d'entreprise gouverné pour **GenAI Enterprise Lab SAS**.

## Mission

Construire et maintenir un système capable de :

> retrouver la bonne information, dans la bonne version, pour la bonne personne, avec des sources vérifiables.

## État actuel

- Phase 0 — bootstrap : terminée
- Phase 1 — organisation / identité / ACL-RBAC-ABAC : terminée
- Phase 2 — dataset documentaire synthétique : terminée
- Phase 3 — Cloudflare R2 + Docling sur Google Cloud Run : validée
- Phase 4 — PostgreSQL + pgvector + recherche hybride + autorité documentaire + Claude + LLM-as-a-Judge : démo fonctionnelle

Le catalogue modélise **5 000 ressources documentaires**. La démo interactive utilise un sous-ensemble contrôlé réellement chargé, chunké et indexé.

## Architecture

- Object storage : Cloudflare R2, juridiction UE
- Parsing documentaire : Docling
- Compute documentaire : Google Cloud Run Jobs
- Build : Google Cloud Build
- Registry : Google Artifact Registry
- Secrets cloud : Google Secret Manager
- Administration : Google Cloud Shell
- Registry / metadata / retrieval : PostgreSQL + pgvector
- Decision contract : adaptateur local compatible Jev
- LLM de réponse : Claude
- Embeddings : OpenAI
- Identity cible : Entra ID ; mock identity en DEV
- Security engine : ACL + RBAC + ABAC déterministes
- GitHub : code, schémas, tests et documentation uniquement

## Security invariant

TOUJOURS :

Identity -> Authorization -> Candidate filtering -> Retrieval/Reranking -> LLM

JAMAIS :

Retrieval -> LLM -> "Peut-il voir ce document ?"

Le LLM, Jev et le LLM-as-a-Judge ne prennent jamais de décision ALLOW/DENY.

### État exact de la démo Phase 4

Le chemin SQL interactif applique actuellement les **ACL avant le ranking**.

Le moteur déterministe Python supporte déjà :

ACL -> RBAC -> ABAC

mais RBAC et ABAC ne sont pas encore branchés sur le chemin SQL interactif. Ne jamais prétendre le contraire dans la documentation ou une démo.

La résolution d'autorité et les shortcuts doivent rester dans le même périmètre ACL que le retrieval.

Réponse standard de refus :

> 🔒 Cette information appartient à une catégorie documentaire restreinte à laquelle votre profil n'a pas accès.

## Retrieval

Recherche hybride :

- PostgreSQL Full-Text Search / TSVECTOR / GIN
- embeddings 1536 dimensions
- pgvector / HNSW / cosine distance
- guardrail de similarité sémantique actuel : >= 0.50
- Reciprocal Rank Fusion (RRF), constante 60

Le seuil 0.50 est calibré pour la démo actuelle ; ce n'est pas une valeur universelle de production.

## Versioning et autorité

Toujours distinguer :

Version chronologique != Validité métier != Autorité documentaire

La résolution d'autorité utilise notamment :

1. authority_level
2. valid_from décroissant
3. created_at décroissant

## Jev

Le code actuel utilise un **adaptateur local déterministe compatible avec le contrat Jev**.

Il fournit :

- intent
- shortcut
- confidence
- risk
- needs_retrieval
- needs_authority_resolution

Ne pas présenter cet adaptateur comme un appel à un service Jev externe réel tant que `JEV_ENABLED` n'est pas branché à une API réelle.

Jev ne décide jamais des droits d'accès.

## Claude

Claude intervient uniquement après filtrage des sources autorisées.

Règles :

- répondre uniquement à partir du contexte fourni ;
- ne pas inventer une information absente ;
- respecter AUTHORITY_DECISION ;
- citer les `document_id` ;
- signaler explicitement des preuves insuffisantes.

## LLM-as-a-Judge

Le Judge évalue :

- relevance
- faithfulness
- completeness
- conflict awareness
- overall
- verdict PASS / REVIEW / FAIL

Le Judge n'a aucun pouvoir d'autorisation.

## Cloud et données

- Le corpus massif ne doit pas être versionné dans Git.
- Les documents cloud restent dans R2.
- Les secrets restent dans Secret Manager ou dans `.env` local ignoré par Git.
- Ne jamais imprimer, commiter ou copier des clés API.
- `data/seed/` contient uniquement des données synthétiques reproductibles et légères.

## Qualité

Avant tout jalon important :

```powershell
python -m pytest -q
python -m ruff check .
python -m mypy src --ignore-missing-imports
```

GitHub Actions exécute également ces contrôles sur `main` et les pull requests.

## Démo principale

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_rag_enterprise.py
```

Scénario de référence :

- client : Axion Solutions
- document faisant foi : DOC-01346
- délai de paiement : 45 jours calendaires
- conflit documentaire : détecté
- réponse : sourcée
- Judge : PASS sur la démo validée

## Shortcuts

Raccourcis actuellement disponibles dans les scripts de démonstration :

- `/contrat`
- `/conflits`
- `/sources`
- `/completude`
- `/signatures mois`

Les shortcuts documentaires doivent appliquer les ACL avant d'afficher une source ou une décision d'autorité.

## Interdictions

- ne jamais contourner ACL/RBAC/ABAC ;
- ne jamais envoyer une source interdite à Claude ;
- ne jamais stocker un secret dans Git ;
- ne jamais annoncer une intégration réelle qui n'existe que sous forme d'adaptateur ;
- ne jamais traiter le LLM-as-a-Judge comme une preuve de sécurité ;
- ne jamais supprimer ou écraser une donnée métier sans étape explicite et traçable.
