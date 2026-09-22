# CLAUDE.md — RAG Enterprise Lab

Tu travailles sur **RAG Enterprise Lab**, un projet de démonstration entreprise réaliste.

## Mission
Construire progressivement un système de connaissance capable de :
> retrouver la bonne information, dans la bonne version, pour la bonne personne, avec des sources vérifiables.

## Contexte métier
Entreprise fictive : **GenAI Enterprise Lab SAS**
- 120 collaborateurs
- activités : Data, BI, IA, Engineering, Consulting
- 65 clients actifs environ
- 5 000 ressources documentaires finales

## Architecture imposée
- Object storage : Cloudflare R2, juridiction EU
- Parsing documentaire : Docling
- Registry + metadata + vector store : PostgreSQL + pgvector
- Decision layer : Jev via adapter
- LLM : Claude via adapter
- Identity : Entra ID cible, mock identity en DEV
- Security : ACL + RBAC + ABAC avant retrieval final / avant LLM
- HTTP edge : Apache / reverse proxy
- Development : cloud-first, pas de corpus volumineux local

## Rôle des composants

### Docling
Lire et structurer : texte, titres, tableaux, pages, structure, OCR si nécessaire.

### Jev
Décisions bornées et typées :
- intent routing
- classification documentaire
- scoring
- confidence
- anomaly / conflict candidate
- risk qualification

Jev ne doit JAMAIS décider :
- si un utilisateur peut lire un document ;
- d'une suppression RGPD définitive ;
- d'une règle légale irréversible.

### PostgreSQL
Source de vérité calculable :
- documents
- versions
- statuts
- signatures
- contrats attendus
- commerciaux
- montants
- completeness
- ACL
- audit

### Claude
- raisonnement sur contexte autorisé
- synthèse
- explication
- réponses sourcées
- aucune décision d'autorisation

## Security invariant
TOUJOURS :
Identity -> Policy/ACL -> Candidate filtering -> Retrieval/Reranking -> LLM

JAMAIS :
Retrieval -> LLM -> "Peut-il voir ce document ?"

Réponse standard en cas de refus :
> 🔒 Cette information appartient à une catégorie documentaire restreinte à laquelle votre profil n'a pas accès.

## Phase 0 — Bootstrap uniquement
Tu dois :
1. lire tous les fichiers du repo ;
2. vérifier la cohérence de l'arborescence ;
3. installer uniquement les dépendances légères de développement ;
4. ne pas installer Docling localement par défaut ;
5. vérifier les modèles Pydantic ;
6. exécuter les tests ;
7. corriger les erreurs éventuelles sans élargir le scope ;
8. produire `docs/phase-reports/PHASE-0-REPORT.md` ;
9. faire un commit : `chore: bootstrap RAG Enterprise Lab architecture`

### Interdictions Phase 0
- ne pas générer les 5 000 documents ;
- ne pas créer de base distante ;
- ne pas créer de bucket R2 ;
- ne pas demander de clé API dans le code ;
- ne pas lancer d'OCR ;
- ne pas implémenter encore le frontend ;
- ne pas simuler une réussite si un test échoue.

## Definition of Done Phase 0
- `pytest` passe
- aucun secret versionné
- `.env.example` complet
- configuration DEV/UAT/PROD définie
- modèles métier de base définis
- ACL invariant testé
- taxonomie validée
- shortcuts enregistrés
- rapport Phase 0 présent
