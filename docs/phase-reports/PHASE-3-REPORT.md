# Phase 3 — Cloud Storage & Document Ingestion

Date : 2026-09-23
Périmètre exécuté : correctif documentaire préalable (BUSINESS_REGISTRY) +
Phase 3 (adapter R2, génération physique déterministe, pipeline
upload/ingestion, quarantaine, idempotence, dry-run progressif).

## 0. Correctif documentaire préalable

Comme demandé, toute mention affirmant que « PostgreSQL Phase 1 » existe
déjà a été corrigée. La source de vérité actuelle pour le statut client
(scénario `CUSTOMER_STATUS`) est **BUSINESS_REGISTRY**, implémentée en
Phase 1/2 par les fichiers seed structurés (`data/seed/*.json`) ; PostgreSQL
en sera l'implémentation persistante dans une phase ultérieure. Fichiers
corrigés : `generation/conflict_generator.py`, `docs/scenarios/README.md`,
`docs/phase-reports/PHASE-2-REPORT.md`, `tests/test_document_conflicts.py`
(préfixe `ground_truth_source_document_id` : `CRM:` → `BUSINESS_REGISTRY:`).
Dataset Phase 2 régénéré, 73/73 tests Phase 0-2 toujours au vert avant de
démarrer la Phase 3. Commit séparé : `docs: clarify business registry
source of truth`.

## 1. Credentials R2 — état constaté AVANT toute action

Aucun fichier `.env` et aucune variable d'environnement `R2_*` ne sont
présents dans cet environnement (vérifié explicitement avant d'écrire le
moindre code de provisioning). Conformément à CLAUDE.md Phase 3 :

**Statut : `BLOCKED_BY_CREDENTIALS`.**

- Le code complet a été implémenté (adapter réel `R2StorageAdapter` inclus).
- Aucune ressource distante (bucket, objet) n'a été créée ni supposée exister.
- Tous les tests ont été exécutés en mode offline/mock
  (`InMemoryObjectStore`, `MockDoclingAdapter`).
- Checklist de déblocage (affichée aussi par
  `scripts/phase3_ingest.py` quand `--dry-run` n'est pas utilisé) :

```
BLOCKED_BY_CREDENTIALS — R2 credentials are not configured.
Checklist to unblock remote provisioning:
  [ ] R2_ENDPOINT
  [ ] R2_BUCKET
  [ ] R2_ACCESS_KEY_ID
  [ ] R2_SECRET_ACCESS_KEY
```

## 2. Tests — PASS / FAIL

### Tests unitaires (offline/mock)

Commande : `pytest -v`

**117 PASSED, 0 FAILED, 1 SKIPPED.** Le seul test sauté est le test
d'intégration réel (§3), correctement `skipped` (pas d'échec) en l'absence
de credentials, conformément à l'exigence « ne jamais faire échouer les
tests unitaires parce qu'un compte cloud n'est pas configuré ».

Couverture des 17 catégories demandées, toutes vertes :

| Catégorie | Fichier |
|---|---|
| R2 adapter mock | `test_r2_adapter.py` |
| Bucket key generation | `test_bucket_layout.py` |
| Deterministic content generation | `test_document_content_generation.py` |
| Checksum | `test_document_content_generation.py`, `test_processing_record.py` |
| Idempotency | `test_ingestion_pipeline.py::test_upload_is_idempotent_on_rerun` |
| Overwrite protection | `test_ingestion_pipeline.py::test_overwrite_protection_on_content_conflict` |
| Cleanup tempfile | `test_temp_guard.py`, `test_ingestion_pipeline.py::test_cleanup_tempfile_after_each_upload` |
| MAX_LOCAL_TEMP_MB | `test_temp_guard.py::test_max_local_temp_mb_stop_cleanup_error`, `test_ingestion_pipeline.py::test_max_local_temp_mb_stops_the_whole_run` |
| Docling adapter interface | `test_docling_adapter.py` |
| Quarantine routing | `test_ingestion_pipeline.py::test_ingest_quarantine_routing_for_unsupported_format` |
| Unsupported format | `test_docling_adapter.py::test_mock_adapter_raises_on_unsupported_format` |
| Corrupted document | `test_docling_adapter.py::test_mock_adapter_raises_on_empty_content` (+3 variantes) |
| No credentials in logs | `test_ingestion_pipeline.py::test_no_credentials_appear_in_audit_events` |
| Dry-run creates zero remote objects | `test_ingestion_pipeline.py::test_dry_run_creates_zero_remote_objects` |
| Limit N respected | `test_ingestion_pipeline.py::test_limit_n_is_respected` |
| Processed artifacts structure | `test_ingestion_pipeline.py::test_ingest_processed_artifacts_structure` (+ tables.json) |

Qualité complémentaire :
- `ruff check .` → **All checks passed!**
- `mypy src` → **Success: no issues found in 44 source files.**

### Tests d'intégration réels (Cloudflare)

Commande : `pytest -m integration -v`

**0 PASSED, 1 SKIPPED.** `test_r2_integration.py::test_real_r2_put_head_get_delete_roundtrip`
est marqué `@pytest.mark.integration` et `skipif(not credentials_available(...))` —
sauté proprement, `BLOCKED_BY_CREDENTIALS`.

## 3. Taille locale du repository

| Emplacement | Taille |
|---|---:|
| `data/` (Phase 1 + Phase 2 seed + 11 exemples) | ≈ 5,6 Mo |
| Fichiers temporaires laissés après les runs | **0 octet** (nettoyage vérifié par test) |

Le corpus complet (5000 documents physiques) n'a jamais existé localement
au-delà de la durée d'un seul fichier temporaire à la fois par document
(généré → uploadé (mock) → supprimé immédiatement).

## 4. Run complet offline (mock, seed=142, 5000 documents)

Puisque le provisioning réel est bloqué, la validation à pleine échelle a
été effectuée avec `InMemoryObjectStore` + `MockDoclingAdapter` (aucun
réseau, aucune écriture hors `data/`inchangée — voir §3).

### `generate_and_upload` (5000/5000)

| Métrique | Valeur |
|---|---:|
| processed | 5000 |
| uploaded | 5000 |
| skipped | 0 |
| conflicts | 0 |
| quarantined | 0 |
| failed | 0 |
| bytes_uploaded | 4 030 129 |
| temp_disk_current_mb | 0.0 |
| **temp_disk_peak_mb** | **0.0018** (un seul fichier temporaire à la fois) |
| duration_seconds | 8.09 |

### `ingest` (Docling mock, 5000/5000)

| Métrique | Valeur |
|---|---:|
| processed | 5000 |
| uploaded (= documents Docling traités avec succès) | 5000 |
| skipped | 0 |
| quarantined | 0 |
| failed | 0 |
| duration_seconds | 0.34 |

Aucune anomalie de contenu synthétique n'a déclenché la quarantaine sur
cette exécution complète (les scénarios de quarantaine sont testés
individuellement et de façon déterministe — §2). Validation progressive
préalable en `--dry-run` : paliers 1 → 10 → 50 → 500 → 5000, tous réussis
(0 objet R2 créé à chaque palier).

### Structure du bucket obtenue (mock)

```
raw/               5000 objets
  hr/                950
  legal/             850
  clients/           900
  pricing/           450
  technical/         850
  projects/          600
  finance/           400
processed/        15824 objets
  {document_id}/document.json    (5000)
  {document_id}/content.md       (5000)
  {document_id}/metadata.json    (5000)
  {document_id}/tables.json      (824 — documents csv/xlsx uniquement)
quarantine/           0 objets
```

## 5. Documents effectivement uploadés / traités (R2 réel)

**0** — `BLOCKED_BY_CREDENTIALS`. Voir §4 pour les chiffres de la
validation mock à pleine échelle, qui démontre que le pipeline fonctionne
correctement de bout en bout et est prêt pour un run réel dès que les
credentials seront fournis.

## 6. Livrables

### Domaine
`domain/processing.py` (ProcessingStatus, QuarantineReason, ProcessingRecord,
AuditEvent).

### Storage
`storage/bucket_layout.py`. `adapters/r2.py` étendu (ObjectStorePort sync,
ObjectHead, InMemoryObjectStore, R2StorageAdapter, credentials_available).

### Docling
`adapters/docling.py` étendu (DocumentParserPort sync, MockDoclingAdapter,
DoclingWorkerAdapter, UnsupportedFormatError, CorruptedDocumentError).

### Génération physique
`generation/document_format_rules.py`, `generation/document_content_generator.py`
(7 formats, aucune dépendance ajoutée).

### Pipeline
`ingestion/temp_guard.py` (TempFileGuard, MAX_LOCAL_TEMP_MB),
`ingestion/stats.py` (RunStats, RunResult), `ingestion/pipeline.py`
(`generate_and_upload`, `ingest`).

### Script
`scripts/phase3_ingest.py` (`generate_and_upload` / `ingest`,
`--dry-run`, `--limit N`, checklist BLOCKED_BY_CREDENTIALS).

### Tests (10 fichiers, 45 tests)
`test_bucket_layout.py`, `test_r2_adapter.py`, `test_docling_adapter.py`,
`test_document_content_generation.py`, `test_temp_guard.py`,
`test_ingestion_pipeline.py`, `test_processing_record.py`,
`test_r2_integration.py` (marker `integration`).

### Documentation
`docs/storage/README.md`, `docs/ingestion/README.md` (+ schéma Mermaid
Manifest→Generator→Temp→R2 Raw→Cleanup), `docs/docling/README.md` (+ schéma
Mermaid R2 Raw→Docling→Normalization→Processed/Quarantine),
`docs/quarantine/README.md`, `docs/phase-reports/PHASE-3-REPORT.md` (ce
document).

## 7. Points bloquants

1. **`BLOCKED_BY_CREDENTIALS`** (le seul blocage réel) : aucune ressource
   Cloudflare R2 n'existe. Fournir `R2_ENDPOINT`, `R2_BUCKET`,
   `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (variables d'environnement,
   jamais dans Git) pour débloquer le provisioning réel et l'exécution des
   tests d'intégration.
2. **`DoclingWorkerAdapter` non implémenté fonctionnellement** — par
   conception : Docling doit être installé uniquement dans l'environnement
   worker dédié (non provisionné dans cette session). L'adapter échoue avec
   un message explicite (`RuntimeError`) s'il est appelé sans `docling`
   installé ; `MockDoclingAdapter` couvre tout le pipeline testable ici.

Aucune interdiction Phase 3 n'a été franchie : pas de copie locale
permanente des 5000 documents, pas de cache Docling non borné, pas
d'embeddings, pas d'index vectoriel, pas de dump complet du corpus, pas de
credential codé en dur, pas de secret dans les logs, pas de LLM, pas de
Jev, pas de PostgreSQL, pas de pgvector.

## 8. Commit

Commit réalisé : `feat: build cloud document storage and docling ingestion`.

---

**La Phase 3 est terminée (code complet, tests offline verts, provisioning
distant BLOCKED_BY_CREDENTIALS documenté). En attente de validation
explicite avant de démarrer la Phase 4.**
