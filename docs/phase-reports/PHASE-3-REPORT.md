# Phase 3 — Cloud Storage & Document Ingestion

Date de clôture : 2026-09-24  
Statut : **COMPLETED**

## 1. Objectif

Mettre en place une chaîne documentaire cloud réaliste et contrôlée :

`Manifest -> génération physique -> Cloudflare R2 EU -> Cloud Run Job Paris -> Docling -> R2 processed/quarantine`

Contraintes respectées :

- aucun corpus de 5000 documents matérialisé durablement en local ;
- stockage objet privé en juridiction UE ;
- worker Docling éphémère ;
- secrets hors Git ;
- idempotence par checksum ;
- quarantaine explicite ;
- aucune génération d'embeddings à ce stade ;
- aucune décision d'autorisation confiée au LLM.

## 2. Stockage Cloudflare R2

Bucket privé :

`rag-enterprise-lab`

Juridiction :

`European Union`

Le manifest documentaire Phase 2 a été publié dans :

`manifests/document_manifest.json`

avec contrôle SHA-256 effectué après upload.

Les documents bruts sont stockés sous :

`raw/{domain}/{document_id}.{extension}`

Les résultats Docling sont écrits sous :

`processed/{document_id}/`

avec selon le type de document :

- `content.md`
- `document.json`
- `metadata.json`
- `tables.json` lorsqu'une structure tabulaire est extraite

Les documents en erreur peuvent être routés vers :

`quarantine/`

## 3. Worker Docling Google Cloud Run

Projet GCP :

`rag-enterprise-lab`

Région :

`europe-west9` — Paris

Cloud Run Job :

`rag-docling-worker`

Configuration validée :

- 2 vCPU
- 8 GiB RAM
- timeout 900 s
- max retries 0
- exécution éphémère
- traitement CPU
- un document ciblable avec `DOCUMENT_ID`

Service account dédié :

`rag-docling-worker@rag-enterprise-lab.iam.gserviceaccount.com`

Les credentials R2 sont fournis exclusivement via Google Secret Manager :

- `r2-endpoint`
- `r2-bucket`
- `r2-access-key-id`
- `r2-secret-access-key`

Le service account dispose uniquement du droit nécessaire de lecture de ces secrets.

## 4. Image de production validée

Repository Artifact Registry :

`europe-west9-docker.pkg.dev/rag-enterprise-lab/rag-docling-worker`

Image validée :

`v6`

Digest :

`sha256:2df2d1e3cc24a5f29969b7598982ed55bbfdf749d6a145b9ab44e2a3be2584cb`

Le Dockerfile utilise notamment :

- Python 3.12 slim Bookworm épinglé par digest ;
- PyTorch CPU ;
- torchvision CPU compatible ;
- Docling ;
- bibliothèques système requises par OpenCV/PDF/OCR.

Les anciennes images intermédiaires ont été supprimées afin de limiter le stockage Artifact Registry.

## 5. Correctifs techniques validés pendant les smoke tests

### 5.1 Idempotence DOCX/XLSX/PPTX

Le générateur Office utilisait initialement le timestamp courant dans les archives ZIP.

Conséquence : deux générations logiquement identiques pouvaient produire des checksums différents et provoquer un conflit R2 au lieu d'un `SKIP`.

Correction :

- timestamp ZIP fixe ;
- ordre déterministe ;
- test de régression byte-for-byte.

### 5.2 Conservation du DoclingDocument complet

Le pipeline initial ne persistait qu'une représentation minimale du résultat.

Correction :

`ParsedDocument` transporte désormais le résultat complet de :

`document.export_to_dict()`

`document.json` conserve donc la structure Docling réelle :

- textes ;
- provenance ;
- body ;
- pages ;
- références internes ;
- métadonnées structurelles.

### 5.3 Extraction des tableaux

L'utilisation de `TableItem.export_to_dict()` n'était pas compatible avec la version Docling exécutée.

Correction :

les tables sont converties via :

`table.export_to_dataframe(doc=document)`

puis sérialisées dans `tables.json`.

### 5.4 PDF / OCR

Les premiers essais PDF ont révélé successivement :

- incompatibilité torch / torchvision ;
- dépendance système `libxcb.so.1` absente.

Corrections intégrées dans l'image v6 :

- versions CPU compatibles de torch et torchvision ;
- bibliothèques système X11/OpenCV nécessaires ;
- RapidOCR fonctionnel sur CPU.

## 6. Formats réellement validés sur Cloud Run

### DOCX

Document : `DOC-00003`  
Résultat : **SUCCESS**

Artefacts Docling réels créés dans R2.

### XLSX

Document : `DOC-02703`  
Résultat : **SUCCESS**

Extraction validée :

- `content.md`
- `document.json`
- `metadata.json`
- `tables.json`

### PDF

Document : `DOC-03226`  
Résultat : **SUCCESS**

OCR RapidOCR exécuté sur CPU.

Le `document.json` contient notamment les informations de page, bounding boxes et provenance Docling.

### PPTX

Document : `DOC-04002`  
Résultat : **SUCCESS**

Artefacts structurés créés dans R2.

### Matrice de validation

| Format | Cloud Run | Docling réel | R2 processed | Tables |
|---|---:|---:|---:|---:|
| DOCX | PASS | PASS | PASS | N/A |
| XLSX | PASS | PASS | PASS | PASS |
| PDF | PASS | PASS | PASS | N/A |
| PPTX | PASS | PASS | PASS | N/A |

## 7. Validation offline

Le pipeline avait préalablement été validé sur les 5000 entrées du manifest avec les adapters offline/mock.

Cette validation a couvert notamment :

- génération ;
- upload ;
- checksum ;
- idempotence ;
- protection contre l'écrasement ;
- nettoyage temporaire ;
- limitation disque local ;
- quarantaine ;
- formats invalides ;
- dry-run ;
- limites de batch ;
- audit sans exposition de secrets.

Le corpus physique complet n'est pas conservé sur le poste local.

## 8. Validation qualité finale locale

Après rapatriement des correctifs Cloud Shell dans le repository Windows :

```text
pytest:
127 passed in 13.39s

ruff:
All checks passed!

mypy:
Success: no issues found in 45 source files
```

Le repository était propre après commit.

## 9. Commit de clôture technique

Commit :

`68e6c0d`

Message :

`feat(phase3): add Cloud Run Docling worker and deterministic ingestion`

Ce commit contient notamment :

- worker Cloud Run ;
- Dockerfile ;
- configuration cloud ;
- adapter Docling réel ;
- conservation du DoclingDocument ;
- extraction XLSX ;
- pipeline enrichi ;
- génération Office déterministe ;
- tests worker et tests de régression ;
- `.dockerignore` ;
- `.gcloudignore`.

## 10. Décision de volumétrie

La Phase 3 ne lance volontairement pas un traitement réel des 5000 documents.

Les quatre familles de formats principales ont été validées individuellement dans l'environnement réel.

Les campagnes plus importantes — 10, 50, 100 documents puis éventuellement davantage — sont reportées aux phases de performance / évaluation afin :

- de mesurer les temps de traitement ;
- de mesurer le coût réel ;
- d'éviter des dépenses cloud inutiles pendant la construction ;
- de distinguer validation fonctionnelle et benchmark de charge.

## 11. Points non bloquants / backlog

Les éléments suivants ne bloquent pas la Phase 4 :

1. RapidOCR peut télécharger certains modèles lors d'un démarrage à froid.
2. Le téléchargement Hugging Face peut afficher un warning d'authentification non bloquant.
3. Une ligne de footer synthétique XLSX peut apparaître comme ligne de table et pourra être normalisée ultérieurement.
4. Le corpus réel complet de 5000 documents n'a volontairement pas été traité par Docling.
5. Les objets historiques de quarantaine issus des essais techniques doivent être conservés ou nettoyés explicitement selon la politique d'audit retenue.

## 12. Critères d'acceptation Phase 3

| Critère | Statut |
|---|---|
| R2 privé en UE | PASS |
| Manifest 5000 publié | PASS |
| Secrets hors Git | PASS |
| Service account dédié | PASS |
| Worker Cloud Run Paris | PASS |
| Docling réel | PASS |
| DOCX réel | PASS |
| XLSX réel | PASS |
| PDF + OCR réel | PASS |
| PPTX réel | PASS |
| DoclingDocument structuré conservé | PASS |
| Extraction tableaux | PASS |
| Idempotence | PASS |
| Quarantaine | PASS |
| Pas de corpus massif local | PASS |
| Tests unitaires | PASS — 127 |
| Ruff | PASS |
| MyPy | PASS |
| Repository Git propre | PASS |

---

# Conclusion

**PHASE 3 — COMPLETED**

La chaîne documentaire réelle est opérationnelle :

`R2 EU -> Cloud Run Paris -> Docling -> processed/quarantine`

Les quatre formats représentatifs ont été exécutés avec succès dans l'environnement cloud réel.

La prochaine étape architecturale est :

**Phase 4 — PostgreSQL + pgvector + Hybrid Retrieval.**
