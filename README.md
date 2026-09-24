# RAG Enterprise Lab

Blueprint technique d'un RAG d'entreprise gouverné pour **GenAI Enterprise Lab**.

## Objectif

> Retrouver la bonne information, dans la bonne version, pour la bonne personne, avec des sources vérifiables.

Cas simulé :

- 120 collaborateurs
- 5 000 ressources documentaires modélisées
- contrats clients / prestataires / RH
- conventions, grilles tarifaires, procédures, runbooks
- complétude documentaire
- conflits de versions
- ACL / RBAC / ABAC
- RGPD
- audit et évaluation
- cas métier phare : clôture mensuelle des signatures commerciales

Pour accélérer la démonstration, le catalogue conserve **5 000 ressources documentaires**, tandis que l'exécution interactive utilise un sous-ensemble contrôlé de documents réellement parsés, chunkés et indexés.

---

# Architecture

Le projet suit une architecture **cloud-first** : le poste de développement ne doit pas contenir le corpus documentaire complet.

## Architecture logicielle : Cloud FIRST

> GitHub README ne supporte pas de carrousel interactif JavaScript. Cette vue en **cartes horizontales** joue le même rôle visuel : elle permet de comprendre rapidement chaque brique et sa fonction.

| ☁️ Cloudflare R2 | 🏗️ Cloud Build | 📦 Artifact Registry | 🔐 Secret Manager | ⚙️ Cloud Run Jobs | 🖥️ Cloud Shell |
|---|---|---|---|---|---|
| Stockage documentaire | Build de l'image Docker | Registry des images | Secrets R2 | Exécution Docling | Administration GCP |
| `raw /` `processed /` `quarantine /` | Contexte de build minimal | Image worker versionnée | Injection au runtime | Parsing / OCR / tables | `gcloud`, logs, diagnostics |
| Juridiction UE | Publication automatisée | Digest traçable | Aucun secret dans Git | Compute éphémère | Pas une brique runtime |

### Flux cloud-first

```text
Documents
   │
   ▼
Cloudflare R2 / raw
   │
   ▼
Google Cloud Run Job
   │
   ├── image depuis Artifact Registry
   ├── secrets depuis Secret Manager
   └── worker Docling
   │
   ▼
Cloudflare R2 / processed
   │
   ▼
PostgreSQL + pgvector
   │
   ▼
RAG gouverné
```

Cloud Build construit l'image du worker avant publication dans Artifact Registry. Cloud Shell sert à administrer, déployer et diagnostiquer l'ensemble des services Google Cloud.

```text
                                   UTILISATEUR
                                       │
                                       ▼
                              Question / Shortcut
                                       │
                                       ▼
                              Jev Decision Layer
                         intent / confidence / risk
                                       │
                                       ▼
                              Identity Context
                         groups / roles / clearance
                                       │
                                       ▼
                           Security Guardrail
                            ACL / RBAC / ABAC
                                       │
                                       ▼
                         PostgreSQL + pgvector
                    documents / versions / chunks / ACL
                           │                 │
                           │                 │
                    Full-Text Search      pgvector
                    TSVECTOR + GIN      HNSW + cosine
                           │                 │
                           └────────┬────────┘
                                    ▼
                            Hybrid Retrieval
                                    │
                                    ▼
                           Relevance Guardrail
                                    │
                                    ▼
                                   RRF
                                    │
                                    ▼
                        Version & Authority Resolution
                                    │
                                    ▼
                            Authorized Context
                                    │
                                    ▼
                                  Claude
                                    │
                                    ▼
                            Output Guardrail
                                    │
                                    ▼
                           LLM-as-a-Judge
                                    │
                                    ▼
                             Final Response
```

## Parcours utilisateur

Le parcours ci-dessous décrit ce qui se passe entre la question saisie par l'utilisateur et la réponse métier finale.

```text
❓ Question utilisateur
   >>
🧠 Jev — Decision Layer
   - détecte l’intention
   - score la confiance
   - route vers shortcut ou retrieval
   >>
👤 Identity Context
   - utilisateur
   - rôles
   - groupes
   - clearance
   >>
🛡️ Security Guardrail
   - ACL / RBAC / ABAC
   - filtre avant retrieval
   >>
🔎 Hybrid Retrieval
   - PostgreSQL Full-Text Search
   - embeddings + pgvector
   >>
🎯 Relevance Guardrail
   - élimine les candidats trop faibles
   >>
📊 RRF
   - fusionne lexical_rank + semantic_rank
   - calcule hybrid_score
   >>
⚖️ Version & Authority Resolution
   - version applicable
   - document faisant foi
   - conflit éventuel
   >>
📄 Authorized Context
   - chunks utiles
   - sources autorisées uniquement
   >>
🤖 Claude
   - raisonne sur ce contexte
   - cite les document_id
   - refuse d’inventer
   >>
🛡️ Output Guardrail
   - structure
   - citations
   - contenu sensible
   >>
🧪 LLM-as-a-Judge
   - relevance
   - faithfulness
   - completeness
   - conflict awareness
   >>
📊 Final Response
   - réponse métier
   - sources
   - hybrid score
   - authority
   - conflict flag
   - judge score
```

### Lecture fonctionnelle du parcours

| Étape | Fonction |
|---|---|
| ❓ Question utilisateur | Point d'entrée naturel ou shortcut métier. |
| 🧠 Jev | Comprend l'intention, estime le risque et choisit la route de traitement. |
| 👤 Identity Context | Porte l'identité, les rôles, groupes et niveaux de clearance. |
| 🛡️ Security Guardrail | Applique les droits avant toute exposition de contenu. |
| 🔎 Hybrid Retrieval | Combine recherche lexicale et sémantique. |
| 🎯 Relevance Guardrail | Écarte les résultats trop faibles pour limiter le bruit. |
| 📊 RRF | Fusionne les classements lexical et sémantique. |
| ⚖️ Authority Resolution | Détermine la version juridiquement ou métier applicable. |
| 📄 Authorized Context | Construit le contexte minimal, utile et autorisé. |
| 🤖 Claude | Génère une réponse sourcée à partir du seul contexte autorisé. |
| 🛡️ Output Guardrail | Contrôle la forme, les citations et les risques de fuite. |
| 🧪 LLM-as-a-Judge | Évalue la qualité de la réponse sans intervenir dans l'autorisation. |
| 📊 Final Response | Restitue réponse, sources, score hybride, autorité, conflit et score Judge. |

Le LLM n'est donc **qu'une étape du pipeline**. L'autorisation, le retrieval, la résolution documentaire et l'évaluation sont traités autour de lui.

---

## Cloudflare

### Cloudflare R2 — stockage documentaire

**Rôle :** stocker les documents physiques et les artefacts Docling sans matérialiser le corpus complet sur le poste local.

Bucket :

```text
rag-enterprise-lab
```

Juridiction :

```text
European Union
```

Organisation logique :

```text
manifests/
    document_manifest.json

raw/
    hr/
    legal_contracts/
    pricing/
    technical/
    projects/
    finance/
    ...

processed/
    DOC-xxxxx/
        content.md
        document.json
        metadata.json
        tables.json

quarantine/
    ...
```

R2 assure notamment :

- le stockage des documents originaux ;
- le stockage des artefacts structurés générés par Docling ;
- la séparation `raw / processed / quarantine` ;
- le contrôle par checksum ;
- l'idempotence des uploads ;
- un stockage privé en juridiction UE ;
- l'absence de corpus documentaire massif dans Git ou sur le poste local.

---

## Google Cloud

Le traitement documentaire réel est exécuté dans le projet GCP :

```text
rag-enterprise-lab
```

Région principale :

```text
europe-west9 — Paris
```

Quatre services Google Cloud sont utilisés.

### 1. Cloud Run Jobs

**Rôle :** exécuter le worker Docling à la demande dans un environnement éphémère.

Job :

```text
rag-docling-worker
```

Configuration utilisée :

- 2 vCPU
- 8 GiB RAM
- timeout 900 s
- max retries 0
- traitement CPU
- ciblage d'un document avec `DOCUMENT_ID`

Flux :

```text
Cloudflare R2 / raw
        │
        ▼
Cloud Run Job
        │
        ▼
Docling
        │
        ├── parsing
        ├── OCR si nécessaire
        ├── structure
        └── extraction de tableaux
        │
        ▼
Cloudflare R2 / processed
```

Cloud Run est utilisé comme **compute éphémère** : aucun worker permanent n'est maintenu en fonctionnement.

### 2. Artifact Registry

**Rôle :** stocker l'image Docker du worker Docling.

Repository :

```text
europe-west9-docker.pkg.dev/rag-enterprise-lab/rag-docling-worker
```

Image validée :

```text
v6
sha256:2df2d1e3cc24a5f29969b7598982ed55bbfdf749d6a145b9ab44e2a3be2584cb
```

L'image contient notamment :

- Python 3.12
- Docling
- PyTorch CPU
- torchvision CPU
- RapidOCR
- dépendances système nécessaires au parsing PDF / OpenCV

Les anciennes images intermédiaires sont supprimées afin de limiter les coûts de stockage.

### 3. Secret Manager

**Rôle :** fournir les secrets R2 au worker Cloud Run sans les stocker dans Git ni dans l'image Docker.

Secrets utilisés :

```text
r2-endpoint
r2-bucket
r2-access-key-id
r2-secret-access-key
```

Service account dédié :

```text
rag-docling-worker@rag-enterprise-lab.iam.gserviceaccount.com
```

Principe appliqué :

```text
Secret Manager
      │
      ▼
Cloud Run Job
      │
      ▼
variables d'environnement runtime
```

Le worker reçoit uniquement les secrets nécessaires à son exécution.

### 4. Cloud Build

**Rôle :** construire l'image Docker du worker Docling avant publication dans Artifact Registry.

Flux :

```text
Code source
    │
    ▼
Cloud Build
    │
    ▼
Docker image
    │
    ▼
Artifact Registry
    │
    ▼
Cloud Run Job
```

Le contexte de build est volontairement minimal grâce à :

```text
.gcloudignore
.dockerignore
```

afin d'éviter d'envoyer le corpus, les environnements virtuels ou les fichiers inutiles pendant les builds.

---

## Google Cloud Shell

**Rôle :** poste d'administration cloud temporaire utilisé pendant la construction et le diagnostic de l'infrastructure.

Cloud Shell a notamment servi à :

- piloter `gcloud` ;
- construire et publier les images ;
- mettre à jour le Cloud Run Job ;
- lancer les exécutions Docling ;
- inspecter les logs ;
- vérifier les secrets sans les exposer ;
- contrôler les digests Artifact Registry ;
- diagnostiquer les dépendances Docker ;
- valider les traitements DOCX / XLSX / PDF / PPTX.

Cloud Shell n'est **pas une brique runtime du RAG**. C'est une console d'exploitation et d'administration.

```text
Développeur
    │
    ▼
Cloud Shell
    │
    ├── Cloud Build
    ├── Artifact Registry
    ├── Secret Manager
    └── Cloud Run Jobs
```

---

## PostgreSQL + pgvector

PostgreSQL est utilisé comme **registre gouverné du RAG**, pas uniquement comme base vectorielle.

Tables principales :

```text
documents
document_versions
document_acl
chunks
audit_events
```

Rôle :

- identité logique des documents ;
- gestion des versions ;
- validité métier ;
- autorité documentaire ;
- relations `supersedes` ;
- ACL par document ;
- chunks exploitables par le RAG ;
- embeddings ;
- journal d'audit.

### Recherche lexicale

```text
PostgreSQL Full-Text Search
→ TSVECTOR
→ index GIN
```

### Recherche sémantique

```text
Embeddings
→ VECTOR(1536)
→ pgvector
→ index HNSW
→ distance cosinus
```

### Recherche hybride

```text
Lexical Search
      +
Semantic Search
      ↓
     RRF
      ↓
Hybrid Score
```

Le guardrail actuel impose également un seuil minimal de pertinence sémantique avant fusion.

---

## Versioning et autorité documentaire

Trois notions sont volontairement séparées :

```text
Version chronologique
≠
Validité métier
≠
Autorité documentaire
```

Exemple réel de démonstration :

```text
DOC-01281
Client Contract — Axion Solutions
        │
        ▼
DOC-01346
Contract Amendment — SIGNED
SIGNED_AMENDMENT
```

Le système peut donc déterminer quel document **fait foi**, même si le document le plus récent n'est pas nécessairement le plus autoritaire.

---

## Jev — Decision Layer

Jev est utilisé comme couche de décision bornée et typée.

Il intervient pour :

- intent routing ;
- détection des shortcuts ;
- scoring de confiance ;
- qualification du risque ;
- décision `shortcut vs retrieval` ;
- indication du besoin de résolution d'autorité.

Jev ne décide **jamais** si un utilisateur peut consulter un document.

Sortie type :

```json
{
  "intent": "GENERAL_RAG",
  "confidence": 0.85,
  "risk": "MEDIUM",
  "needs_retrieval": true,
  "needs_authority_resolution": true
}
```

---

## Claude

Claude intervient **après** :

- l'identité ;
- les ACL ;
- le retrieval ;
- le guardrail de pertinence ;
- la résolution de version / autorité.

Il reçoit uniquement un **Authorized Context**.

Règles :

- répondre uniquement à partir des sources fournies ;
- ne pas inventer une information absente ;
- respecter le document faisant foi ;
- citer les `document_id` ;
- signaler des preuves insuffisantes plutôt que compléter par hallucination.

---

## Guardrails

La démonstration met en place plusieurs guardrails :

### Security Guardrail

```text
ACL / RBAC / ABAC
→ avant retrieval
```

### Relevance Guardrail

```text
cosine similarity >= 0.50
```

### Version / Conflict Guardrail

```text
authority_level
→ valid_from
→ created_at
```

### Output Guardrail

Le modèle ne reçoit que les sources autorisées et doit conserver une réponse sourcée.

---

## LLM-as-a-Judge

Une seconde passe LLM évalue automatiquement la réponse générée.

Critères :

- relevance ;
- faithfulness ;
- completeness ;
- conflict awareness ;
- overall score ;
- verdict `PASS / REVIEW / FAIL`.

Exemple de résultat de la démo :

```text
🎯 Relevance           : 1.00
📚 Faithfulness        : 1.00
📋 Completeness        : 0.95
⚖️ Conflict awareness : 1.00
📊 Overall             : 0.97

✅ Verdict : PASS
```

Le Judge ne participe jamais à l'autorisation.

---

## Shortcuts métier

Le système expose des raccourcis déterministes :

```text
/contrat
/conflits
/sources
/completude
/signatures mois
```

Exemple :

```text
🧭 /signatures mois

📄 Contrats attendus    65
✅ Signés               28
⏳ En cours             19
🆕 À traiter            12
🚫 Échecs                6

📊 Taux signé           43.1 %
```

Les shortcuts déclenchent des calculs métier structurés et ne reposent pas sur une réponse libre du LLM.

---

## GitHub

GitHub contient :

- code Python ;
- migrations SQL ;
- scripts ;
- tests ;
- prompts ;
- configurations ;
- documentation ;
- diagrammes.

GitHub ne contient jamais :

- secrets ;
- clés API ;
- corpus complet de documents physiques ;
- dumps PostgreSQL massifs.

---

## Règles non négociables

1. Never trust the LLM for authorization.
2. ACL/RBAC/ABAC sont évalués avant que le contenu ne soit transmis au LLM.
3. Une information interdite ne doit jamais entrer dans le contexte Claude.
4. Une version plus récente n'est pas forcément la version juridiquement applicable.
5. Toute réponse métier factuelle doit être traçable jusqu'à une source.
6. Les données volumineuses restent cloud.
7. Jev et le LLM-as-a-Judge ne décident jamais des droits d'accès.

---

## Démo actuelle

Le scénario Axion Solutions valide aujourd'hui :

```text
Question naturelle
→ Jev
→ ACL
→ Hybrid Retrieval
→ Relevance Guardrail
→ Authority Resolution
→ Claude
→ LLM-as-a-Judge
→ Final Response
```

Résultat observé :

```text
⚖️ Document faisant foi : DOC-01346
📅 Valid from            : 2026-02-12
💳 Délai applicable      : 45 jours calendaires
⚠️ Conflict detected    : True
🧪 Judge verdict         : PASS
📊 Judge overall         : 0.97
```
