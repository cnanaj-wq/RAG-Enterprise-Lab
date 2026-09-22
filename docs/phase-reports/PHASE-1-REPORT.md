# Phase 1 — Organization & Identity Model

Date : 2026-09-22
Périmètre exécuté : Phase 1 (modèle organisationnel et Identity synthétique),
conformément à la spécification Phase 1 et à `CLAUDE.md`.
Seed de génération : **42** (déterministe, reproductible, idempotent).

## 0. Correctifs Phase 0 préalables

Avant tout développement Phase 1, comme demandé :
1. `config/shortcuts.yml` aligné avec `shortcuts/registry.py` (ajout de `/sources`).
2. Les 7 avertissements `ruff I001` corrigés (`ruff check . --fix`).
3. `pytest` (5/5) + `ruff check .` (clean) exécutés.
4. Commit séparé : `chore: normalize phase 0 configuration`.

## 1. Effectifs calculés (120 exactement)

| Département | Effectif calculé | Effectif attendu |
|---|---:|---:|
| Direction | 6 | 6 |
| Sales / Account | 18 | 18 |
| Consulting | 34 | 34 |
| Data & AI | 20 | 20 |
| Engineering | 16 | 16 |
| IT / Cybersecurity | 8 | 8 |
| RH | 7 | 7 |
| Finance / Legal | 7 | 7 |
| Marketing / Partnerships | 4 | 4 |
| **Total** | **120** | **120** |

Structure Sales / Account (18) : 1 Sales Director, 2 Sales Managers,
8 Account Executives, 4 Key Account Managers, 3 Sales Operations Analysts —
conforme à la spécification.

## 2. Volumes des référentiels

| Référentiel | Volume calculé | Volume attendu |
|---|---:|---:|
| Clients actifs | 65 | 65 |
| Prospects | 120 | 120 |
| Partenaires | 30 | 30 |
| Fournisseurs / prestataires | 80 | 80 |
| Projets (delivery, 1/client actif) | 65 | — |
| Opportunités (1/client actif) | 65 | — |
| Groupes Identity (statiques + dynamiques) | 141 | — |

Détail groupes : 11 statiques + 65 `RAG_CLIENT_{code}` + 65 `RAG_PROJECT_{code}`.

## 3. Exemples — 5 collaborateurs

| employee_id | Nom | Département | Poste | manager_id | security_groups (extrait) |
|---|---|---|---|---|---|
| EMP-0001 | Olivier Fischer | Direction | Chief Executive Officer | — | RAG_ALL_EMPLOYEES, RAG_EXECUTIVE |
| EMP-0007 | Adam Costa | Sales / Account | Sales Director | EMP-0006 | RAG_ALL_EMPLOYEES, RAG_SALES |
| EMP-0021 | Uma Novotny | Sales / Account | Key Account Manager | EMP-0009 | RAG_ALL_EMPLOYEES, RAG_SALES, RAG_CLIENT_C012 |
| EMP-0056 | Mateo Leroy | Consulting | Consultant | EMP-0028 | RAG_ALL_EMPLOYEES, RAG_CONSULTING, RAG_PROJECT_PJ029 |
| EMP-0101 | Yara Lambert | IT / Cybersecurity | IT / Security Analyst | EMP-0095 | RAG_ALL_EMPLOYEES, RAG_IT |

## 4. Exemples — 5 clients actifs

| customer_id | client_code | Nom | Secteur | Segment | Account Manager | Sales Manager | Risque |
|---|---|---|---|---|---|---|---|
| CLI-0001 | C001 | Solace Systems | Retail & E-commerce | SMB | EMP-0010 | EMP-0008 | MEDIUM |
| CLI-0002 | C002 | Axion Consulting | Professional Services | STRATEGIC | EMP-0011 | EMP-0009 | LOW |
| CLI-0003 | C003 | Driftwood Systems | Healthcare & Life Sciences | MID_MARKET | EMP-0012 | EMP-0008 | HIGH |
| CLI-0004 | C004 | Vellum Consulting | Media & Entertainment | MID_MARKET | EMP-0013 | EMP-0009 | LOW |
| CLI-0005 | C005 | Verdant Labs | Telecom | ENTERPRISE | EMP-0014 | EMP-0008 | MEDIUM |

Toutes les personnes et sociétés sont fictives (générées par combinaison,
`src/rag_enterprise_lab/generation/namebank.py`).

## 5. Groupes Identity

**Statiques (11)** : `RAG_ALL_EMPLOYEES`, `RAG_HR`, `RAG_FINANCE`, `RAG_LEGAL`,
`RAG_SALES`, `RAG_IT`, `RAG_DATA_AI`, `RAG_ENGINEERING`, `RAG_EXECUTIVE`,
`RAG_MARKETING`, `RAG_CONSULTING` (ajout, voir § 8).

**Dynamiques** : 65 `RAG_CLIENT_{code}` + 65 `RAG_PROJECT_{code}`, matérialisés
dans `data/seed/identity_groups.json` à partir des patterns
`RAG_CLIENT_{CLIENT_CODE}` / `RAG_PROJECT_{PROJECT_CODE}`.

Détail RBAC / ABAC / moteur d'autorisation : [docs/identity/README.md](../identity/README.md).

## 6. Tests — résultats (33/33 PASS)

| # | Exigence | Test | Résultat |
|---|---|---|---|
| 1 | Exactement 120 collaborateurs | `test_organization.py::test_exactly_120_employees` | **PASS** |
| 2 | Distribution exacte par département | `test_organization.py::test_department_distribution_exact` | **PASS** |
| 3 | Aucun employee_id dupliqué | `test_organization.py::test_no_duplicate_employee_id` | **PASS** |
| 4 | Aucun corporate_email dupliqué | `test_organization.py::test_no_duplicate_email` | **PASS** |
| 5 | manager_id valide | `test_organization.py::test_all_manager_ids_valid` | **PASS** |
| 6 | Aucun cycle hiérarchique | `test_organization.py::test_no_hierarchy_cycle` | **PASS** |
| 7 | Groupes départementaux cohérents | `test_organization.py::test_department_groups_coherent` | **PASS** |
| 8 | Exactement 65 clients actifs | `test_commercial.py::test_exactly_65_active_clients` | **PASS** |
| 9 | Exactement 120 prospects | `test_commercial.py::test_exactly_120_prospects` | **PASS** |
| 10 | Exactement 30 partenaires | `test_commercial.py::test_exactly_30_partners` | **PASS** |
| 11 | Exactement 80 fournisseurs | `test_commercial.py::test_exactly_80_suppliers` | **PASS** |
| 12 | Account manager valide par client actif | `test_commercial.py::test_client_account_manager_valid` | **PASS** |
| 13 | Account manager appartient à Sales | `test_commercial.py::test_account_manager_in_sales` | **PASS** |
| 14 | ACL deny-by-default toujours valide | `test_identity.py::test_acl_deny_by_default_*` (2 tests) | **PASS** |
| 15 | Dataset reproductible même seed | `test_dataset_reproducibility.py::test_dataset_reproducible_with_same_seed` | **PASS** |
| 16 | Aucun secret | `test_repo_hygiene.py::test_no_secrets_in_generated_seed_data` + `test_generated_seed_manifest_has_no_credentials` | **PASS** |
| 17 | Aucun corpus documentaire volumineux local | `test_repo_hygiene.py::test_no_large_local_corpus` + `test_seed_dataset_volume_is_lightweight` | **PASS** |

Tests complémentaires ajoutés (couverture RBAC/ABAC, Finance/Legal, dataset
différent avec un autre seed, exclusion Jev/Claude du moteur d'autorisation,
1 opportunité par client actif, matérialisation des groupes dynamiques) :
16 tests additionnels, tous **PASS**.

**Total : 33/33 PASS, 0 FAIL.** Aucune correction de logique métier n'a été
nécessaire après écriture des tests, à l'exception d'un test lui-même
mal conçu (voir § 8, point 2).

Qualité complémentaire (hors DoD strict) :
- `ruff check .` → **All checks passed!**
- `mypy src` → **Success: no issues found in 22 source files**.

## 7. Fichiers créés / modifiés

### Correctifs Phase 0
- `config/shortcuts.yml` (modifié)
- 7 fichiers reformattés par `ruff --fix` (imports)

### Domaine (`src/rag_enterprise_lab/domain/`)
- `organization.py` (Department, BusinessUnit, EmploymentType, SeniorityLevel,
  Clearance, Employee)
- `commercial.py` (Client, Prospect, Partner, Supplier + enums)
- `delivery.py` (Project, ProjectStatus)
- `sales.py` (Opportunity, SignatureStatus)

### Identity (`src/rag_enterprise_lab/identity/`)
- `groups.py` (groupes statiques, mapping départemental, builders dynamiques)
- `rbac.py` (enum `Role`)

### Sécurité (`src/rag_enterprise_lab/security/`)
- `acl.py` (modifié : extraction de `authorize_groups`, `authorize` inchangé)
- `authorization.py` (nouveau : moteur déterministe ACL → RBAC → ABAC)

### Génération (`src/rag_enterprise_lab/generation/`)
- `namebank.py`, `organization_generator.py`, `commercial_generator.py`,
  `delivery_generator.py`, `sales_generator.py`, `dataset.py`

### Script
- `scripts/generate_phase1_dataset.py`

### Tests (`tests/`)
- `conftest.py`, `test_organization.py`, `test_commercial.py`,
  `test_identity.py`, `test_dataset_reproducibility.py`, `test_repo_hygiene.py`

### Documentation
- `docs/organization/README.md` (+ schéma Mermaid organisation)
- `docs/identity/README.md` (+ schéma Mermaid Identity → RBAC/ABAC → ACL → Resource)
- `docs/data-model/README.md`
- `docs/phase-reports/PHASE-1-REPORT.md` (ce document)

### Données générées
- `data/seed/*.json` (employees, clients, prospects, partners, suppliers,
  projects, opportunities, identity_groups, manifest) — **233 Ko**, très
  inférieur à la limite de 100 Mo.

## 8. Points bloquants / remarques

Aucun point bloquant. Deux écarts assumés et documentés :

1. **Groupe `RAG_CONSULTING` ajouté.** La liste de groupes fournie
   (`RAG_ALL_EMPLOYEES`, `RAG_HR`, `RAG_FINANCE`, `RAG_LEGAL`, `RAG_SALES`,
   `RAG_IT`, `RAG_DATA_AI`, `RAG_ENGINEERING`, `RAG_EXECUTIVE`,
   `RAG_MARKETING`) ne couvre pas le département Consulting, qui représente
   34 collaborateurs (28 % de l'effectif). Comme le test obligatoire #7
   (« groupes départementaux cohérents ») implique que les 9 départements
   aient un groupe ACL cohérent, `RAG_CONSULTING` a été ajouté en suivant la
   convention `RAG_<DÉPARTEMENT>` existante. Sans cet ajout, un tiers de
   l'effectif n'aurait aucun contrôle d'accès départemental — un risque de
   sécurité plus grand qu'un écart de nommage.
2. **Test `test_jev_and_claude_are_never_authorization_dependencies` corrigé
   en cours de route.** La première version cherchait la sous-chaîne "jev"
   dans le code source du moteur d'autorisation, mais mon propre commentaire
   expliquant que « Jev et Claude ne sont jamais consultés » contenait le mot
   et faisait échouer le test à tort. Corrigé pour inspecter les imports
   réels (AST) plutôt que le texte brut — le moteur ne dépend d'aucun module
   `jev`/`claude`.

Aucune interdiction Phase 1 n'a été franchie : pas de document PDF/contractuel
généré, pas de bucket R2, pas de PostgreSQL distant, pas d'installation de
Docling, pas d'appel à Jev, pas d'appel à l'API Claude, aucun corpus
documentaire local volumineux (seuls des fichiers JSON de seed < 250 Ko).

## 9. Commit

Commit réalisé : `feat: build synthetic organization and identity model`.

---

**La Phase 1 est terminée et conforme aux exigences fournies. En attente de
validation explicite avant de démarrer la Phase 2.**
