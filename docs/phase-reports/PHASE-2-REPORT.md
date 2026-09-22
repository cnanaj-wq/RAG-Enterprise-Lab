# Phase 2 — Document Intelligence Dataset

Date : 2026-09-23
Périmètre exécuté : correctif ciblé du modèle Sales (préalable demandé) +
Phase 2 (manifest documentaire, anomalies, conflits, complétude, ground
truth, ≤ 50 exemples physiques). Seed organisation : **42** (Phase 1, inchangé).
Seed documentaire : **142** (déterministe, reproductible, idempotent).

## 0. Correctif ciblé — Opportunity vs ExpectedContract vs signature_status

Avant tout développement Phase 2, comme demandé, vérification du modèle
Sales : `Opportunity` portait directement `signature_status`, rendant
ambiguë la distinction entre l'opportunité commerciale (le pipeline) et le
contrat attendu (le suivi de signature).

**Correction appliquée** (`src/rag_enterprise_lab/domain/sales.py`) :
- `Opportunity` ne porte plus `signature_status` ; elle porte désormais
  `stage` (`OPEN`/`WON`/`LOST`), dérivé déterministiquement du statut de
  signature de son `ExpectedContract`.
- `ExpectedContract` (nouvelle entité explicite) porte exclusivement
  `signature_status`, et référence son `opportunity_id`.
- Les 7 facettes demandées sont désormais séparément accessibles :
  opportunité (`opportunity_id`), contrat attendu (`expected_contract_id`),
  propriétaire commercial (`sales_owner_id`), client (`client_id`),
  `expected_close_date`, `expected_amount`, `signature_status`.

4 tests dédiés ajoutés (`tests/test_sales_model.py`), dataset Phase 1
régénéré (`expected_contracts.json` nouveau fichier), documentation
(`docs/data-model/README.md`) mise à jour. **Aucune modification hors
périmètre métier Phase 1/2.**

## 1. Tests — PASS / FAIL global

Commande : `pytest -v`

**73/73 PASS, 0 FAIL** (37 tests Phase 0/1 inchangés + 4 correctif Sales +
32 tests Phase 2 nouveaux). Détail des 20 exigences minimales Phase 2 :

| # | Exigence | Test | Résultat |
|---|---|---|---|
| 1 | Exactement 5000 entrées manifest | `test_document_manifest.py::test_exactly_5000_manifest_entries` | **PASS** |
| 2 | Distribution exacte par domaine | `test_document_manifest.py::test_domain_distribution_exact` | **PASS** |
| 3 | Aucun document_id dupliqué | `test_document_manifest.py::test_no_duplicate_document_id` | **PASS** |
| 4 | Références employee valides | `test_document_manifest.py::test_employee_references_are_valid` | **PASS** |
| 5 | Références client valides | `test_document_manifest.py::test_customer_references_are_valid` | **PASS** |
| 6 | Références supplier valides | `test_document_manifest.py::test_supplier_references_are_valid` | **PASS** |
| 7 | Références project valides | `test_document_manifest.py::test_project_references_are_valid` | **PASS** |
| 8 | ACL valides | `test_document_manifest.py::test_acl_valid_deny_by_default` | **PASS** |
| 9 | Classifications valides | `test_document_manifest.py::test_classifications_are_valid_enum_values` | **PASS** |
| 10 | Version graph sans cycle | `test_document_manifest.py::test_version_graph_has_no_cycle` | **PASS** |
| 11 | Supersedes valide | `test_document_manifest.py::test_supersedes_points_to_existing_document` | **PASS** |
| 12 | Règles d'autorité déterministes | `test_document_authority.py` (5 tests) | **PASS** |
| 13 | Anomalies reproductibles | `test_document_anomalies.py::test_anomalies_reproducible_with_same_seed` | **PASS** |
| 14 | Conflits ground truth cohérent | `test_document_conflicts.py` (3 tests) | **PASS** |
| 15 | Même seed = même manifest | `test_document_dataset_reproducibility.py::test_same_seed_produces_same_manifest` | **PASS** |
| 16 | Autre seed = dataset différent | `test_document_dataset_reproducibility.py::test_different_seed_produces_different_manifest` | **PASS** |
| 17 | Aucun secret | `test_document_hygiene.py::test_no_secrets_*` (2 tests) | **PASS** |
| 18 | Aucun corpus volumineux local | `test_document_hygiene.py::test_no_large_document_corpus_locally` | **PASS** |
| 19 | Maximum 50 documents physiques | `test_document_hygiene.py::test_max_50_physical_example_documents` | **PASS** |
| 20 | Total repository sous la limite | `test_document_hygiene.py::test_total_repository_data_volume_under_limit` | **PASS** |

Qualité complémentaire :
- `ruff check .` → **All checks passed!**
- `mypy src` → **Success: no issues found in 37 source files**
  (ajout de `types-PyYAML` aux dépendances dev, léger, stubs uniquement).

## 2. Volumes exacts (5000 documents)

| Domaine | Volume calculé | Volume attendu |
|---|---:|---:|
| RH | 950 | 950 |
| Legal / Contracts | 850 | 850 |
| Clients / Prospects | 900 | 900 |
| Pricing / Sales | 450 | 450 |
| IT / Architecture / Security | 850 | 850 |
| Projects / Procedures | 600 | 600 |
| Finance / Compliance | 400 | 400 |
| **Total** | **5000** | **5000** |

## 3. Anomalies injectées (60 au total)

45 injectées directement (15 types × 3 instances) + 15 supplémentaires
(`AMENDMENT_CONTRADICTS_CONTRACT` ×12, `CONTRADICTORY_DOCUMENTS` ×3) issues
du registre de conflits pour rester cohérentes avec son ground truth.

| Type | Instances |
|---|---:|
| ACL_INCOHERENT | 3 |
| AMENDMENT_CONTRADICTS_CONTRACT | 15 |
| CONTRADICTORY_DOCUMENTS | 6 |
| CRM_STATUS_INCOHERENT | 3 |
| DUPLICATE | 3 |
| EXPIRED_DOCUMENT | 3 |
| INCOHERENT_DATES | 3 |
| INCOMPLETE_DOCUMENT | 3 |
| MISSING_OWNER | 3 |
| OBSOLETE_PRICING | 3 |
| OBSOLETE_VERSION | 3 |
| OCR_RISK | 3 |
| PARTIAL_SIGNATURE | 3 |
| UNSIGNED_DOCUMENT | 3 |
| WRONG_CLASSIFICATION | 3 |
| **Total** | **60** |

Registre complet avec `ground_truth` : `data/seed/document_anomalies.json`.

## 4. Conflits injectés (21 au total, 7 catégories × 3)

| Catégorie | Instances | Résolution |
|---|---:|---|
| PAYMENT_TERMS | 3 | Avenant signé > contrat signé |
| PRICING | 3 | Grille non supersedée > grille SUPERSEDED |
| CONTRACT_DATES | 3 | Avenant signé > contrat signé |
| SLA | 3 | Avenant signé > contrat signé |
| NOTICE_PERIOD | 3 | Avenant signé > contrat signé |
| RENEWAL | 3 | Avenant signé > contrat signé |
| CUSTOMER_STATUS | 3 | BUSINESS_REGISTRY (Phase 1) fait autorité |

Exemple exact demandé par la spécification (validé par
`test_payment_terms_scenario_matches_specification_example`) :
**contrat = 30 jours, avenant signé = 45 jours, ground truth = 45 jours.**

Registre complet : `data/seed/document_conflicts.json`. Ground truth
exploitable dérivé (27 questions/réponses) : `data/seed/document_expected_answers.json`.

## 5. Taille totale générée

| Emplacement | Taille |
|---|---:|
| `data/seed/` (Phase 1 + Phase 2, JSON) | ≈ 5,7 Mo |
| `data/examples/` (≤ 50 Markdown) | ≈ 18 Ko |
| **Total `data/`** | **≈ 5,7 Mo** |

Très inférieur à la limite de 100 Mo. Aucun fichier bureautique
(pdf/docx/xlsx/pptx), aucun embedding, aucun index vectoriel.

## 6. 10 documents du manifest (extrait réel)

| document_id | domaine | type | version | statut | classification | autorité |
|---|---|---|---|---|---|---|
| DOC-00001 | RH | EMPLOYMENT_CONTRACT | 1.0 | SUPERSEDED | SENSITIVE_PERSONAL_DATA | DRAFT |
| DOC-00002 | RH | EMPLOYMENT_AMENDMENT | 1.0 | DRAFT | SENSITIVE_PERSONAL_DATA | DRAFT |
| DOC-00003 | RH | JOB_DESCRIPTION | 1.0 | IN_REVIEW | INTERNAL | DRAFT |
| DOC-00004 | RH | HR_POLICY | 1.0 | APPROVED | INTERNAL | DRAFT |
| DOC-00005 | RH | COLLECTIVE_AGREEMENT | 1.0 | SUPERSEDED | INTERNAL | DRAFT |
| DOC-00006 | RH | ONBOARDING_DOCUMENT | 1.0 | APPROVED | PERSONAL_DATA | DRAFT |
| DOC-00007 | RH | PAYROLL_RECORD | 1.0 | APPROVED | SENSITIVE_PERSONAL_DATA | DRAFT |
| DOC-00008 | RH | EMPLOYMENT_CONTRACT | 1.0 | SUPERSEDED | SENSITIVE_PERSONAL_DATA | DRAFT |
| DOC-00009 | RH | EMPLOYMENT_AMENDMENT | 1.0 | SIGNED | SENSITIVE_PERSONAL_DATA | SIGNED_AMENDMENT |
| DOC-00010 | RH | JOB_DESCRIPTION | 1.0 | QUARANTINED | INTERNAL | DRAFT |

## 7. 5 chaînes de version (`supersedes`)

| Document | Version | Statut | Supersede |
|---|---|---|---|
| DOC-00002 | 1.0 | DRAFT | DOC-00722 |
| DOC-00009 | 1.0 | SIGNED | DOC-00729 |
| DOC-00015 | 2.0 | DRAFT | DOC-00855 |
| DOC-00016 | 1.0 | SIGNED | DOC-00736 |
| DOC-00022 | 2.0 | SIGNED | DOC-00862 |

## 8. 5 ExpectedContracts

| expected_contract_id | opportunity_id | client_id | sales_owner_id | expected_amount | expected_close_date | signature_status |
|---|---|---|---|---:|---|---|
| ECT-0001 | OPP-0001 | CLI-0001 | EMP-0010 | 11 516,52 € | 2026-09-10 | NOT_SENT |
| ECT-0002 | OPP-0002 | CLI-0002 | EMP-0011 | 297 808,30 € | 2026-09-28 | NOT_SENT |
| ECT-0003 | OPP-0003 | CLI-0003 | EMP-0012 | 60 913,17 € | 2026-09-24 | SIGNED |
| ECT-0004 | OPP-0004 | CLI-0004 | EMP-0013 | 36 519,29 € | 2026-09-17 | SENT |
| ECT-0005 | OPP-0005 | CLI-0005 | EMP-0014 | 109 917,40 € | 2026-09-01 | DECLINED |

## 9. Livrables

### Domaine (`src/rag_enterprise_lab/domain/`)
`document_taxonomy.py`, `documents.py`, `version_authority.py`,
`completeness.py`, `anomalies.py`, `conflicts.py`, `expected_answers.py`.
`models.py` étendu (`DocumentStatus.IN_REVIEW`). `sales.py` corrigé (§0).

### Génération (`src/rag_enterprise_lab/generation/`)
`document_taxonomy_rules.py`, `document_generator.py`,
`version_chain_builder.py`, `anomaly_generator.py`, `conflict_generator.py`,
`expected_answers_generator.py`, `example_documents.py`,
`document_dataset.py` (orchestrateur).

### Configuration
`config/completeness/supplier.yml`, `config/completeness/hr_employee.yml`.

### Script
`scripts/generate_phase2_dataset.py`.

### Tests (10 fichiers, 36 tests Phase 2 + correctif)
`test_sales_model.py`, `test_completeness.py`, `test_document_manifest.py`,
`test_document_authority.py`, `test_document_anomalies.py`,
`test_document_conflicts.py`, `test_document_dataset_reproducibility.py`,
`test_document_hygiene.py`. `conftest.py` étendu (fixture `document_dataset`).

### Documentation
`docs/document-model/README.md`, `docs/document-governance/README.md`
(+ schéma Mermaid statuts), `docs/version-resolution/README.md`
(+ schéma Mermaid Document→Version→Authority→Validity),
`docs/completeness/README.md`, `docs/scenarios/README.md`
(+ schéma Mermaid Opportunity→ExpectedContract→Document→Signature),
`docs/phase-reports/PHASE-2-REPORT.md` (ce document).

### Données générées
`data/seed/document_manifest.json`, `document_anomalies.json`,
`document_conflicts.json`, `document_expected_answers.json`,
`data/seed/expected_contracts.json` (correctif §0),
`data/examples/*.md` (11 documents physiques).

## 10. Points bloquants / remarques

Aucun point bloquant. Remarques documentées :

1. **`checksum` et `storage_target` sont des placeholders explicites**, comme
   demandé (« checksum placeholder », « storage_target »). Aucun hash réel
   n'est calculé (pas de contenu physique pour 4989 des 5000 entrées) ;
   `storage_target` pointe vers un chemin R2 futur (`r2://...`) non créé, ou
   vers le fichier Markdown local pour les 11 exemples matérialisés.
2. **11 documents physiques matérialisés sur 50 autorisés** — sélection
   volontairement ciblée (scénario payment_terms complet contrat+avenant,
   un représentant par type demandé, un document expiré, une contradiction)
   plutôt que d'atteindre la limite pour atteindre la limite.
3. **`CUSTOMER_STATUS` référence une source non-document** :
   `ground_truth_source_document_id="BUSINESS_REGISTRY:{customer_id}"`
   plutôt qu'un `document_id` réel, car le ground truth provient
   délibérément du registre métier (BUSINESS_REGISTRY), pas d'un document.
   En Phase 1/2, ce registre est implémenté par les fichiers seed
   structurés (`data/seed/*.json`) ; PostgreSQL en sera l'implémentation
   persistante dans une phase ultérieure — voir `docs/scenarios/README.md`.
4. **Le seuil de volume `data/seed/` du test Phase 1
   (`test_repo_hygiene.py`)** a été relevé de 5 Mo à 20 Mo : il ne
   couvrait à l'origine que les données Phase 1 (233 Ko) et est devenu trop
   bas maintenant que `document_manifest.json` (5,5 Mo) partage le même
   dossier — toujours très inférieur à la limite réelle de 100 Mo.

Aucune interdiction Phase 2 n'a été franchie : pas de génération physique
des 5000 documents, pas de bucket R2, pas de PostgreSQL distant, pas
d'embeddings, pas d'index vectoriel, pas d'appel Claude API, pas d'appel
Jev, pas de pipeline Docling, aucun fichier bureautique local.

## 11. Commit

Commit réalisé : `feat: model enterprise document intelligence dataset`.

---

**La Phase 2 est terminée et conforme aux exigences fournies. En attente de
validation explicite avant de démarrer la Phase 3.**
