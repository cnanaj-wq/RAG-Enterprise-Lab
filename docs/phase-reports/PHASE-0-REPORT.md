# Phase 0 — Rapport de Bootstrap

Date : 2026-09-22
Périmètre exécuté : Phase 0 uniquement (bootstrap), conformément à `CLAUDE.md`.

## 1. Lecture et cohérence de l'arborescence

Tous les fichiers du dépôt ont été lus (config, docs, ADR, code source, tests, scripts).
Le fichier `manifest.json` a été comparé à l'arborescence réelle : **cohérent**, aucun fichier
manquant ou en trop.

Fichiers YAML de configuration validés syntaxiquement (chargement PyYAML) :
- `config/document-taxonomy.yml`
- `config/security-groups.yml`
- `config/shortcuts.yml`
- `config/completeness/client.yml`

## 2. Environnement et dépendances

- Python détecté : 3.12.10 (`py -3.12`), conforme à `requires-python = ">=3.12"`.
- Environnement virtuel créé : `.venv/`.
- Installation : `pip install -e ".[dev]"` → dépendances du projet + extra `dev`
  (`pytest`, `pytest-asyncio`, `ruff`, `mypy`).
- **Docling non installé** (extra `ingestion` volontairement ignoré), conformément à
  l'interdiction Phase 0.
- Aucune base distante créée, aucun bucket R2 créé, aucune clé API demandée ou codée en dur,
  aucun OCR lancé, aucun frontend implémenté.

## 3. Vérification des modèles Pydantic

`src/rag_enterprise_lab/domain/models.py` importé et instancié avec succès :
- `Classification` (StrEnum, 6 valeurs)
- `DocumentStatus` (StrEnum, 6 valeurs)
- `DocumentRecord`, `UserContext`, `AccessDecision` (BaseModel Pydantic v2)

`src/rag_enterprise_lab/core/config.py` (`Settings`, `pydantic-settings`) chargé avec succès,
valeurs par défaut cohérentes avec `.env.example`.

## 4. Tests — résultats

Commande : `.venv\Scripts\python.exe -m pytest -v`

| Test | Résultat |
|---|---|
| `tests/test_acl.py::test_access_allowed_on_group_match` | **PASS** |
| `tests/test_acl.py::test_access_denied_without_group_match` | **PASS** |
| `tests/test_acl.py::test_access_denied_when_acl_missing` | **PASS** |
| `tests/test_shortcuts.py::test_signature_shortcut_exists` | **PASS** |
| `tests/test_shortcuts.py::test_commercial_close_shortcut_exists` | **PASS** |

**Résultat global : 5 passed, 0 failed** — aucune correction de code n'a été nécessaire.

L'invariant ACL (`allowed_groups` vide → refus ; intersection groupes utilisateur/document →
autorisation ; aucune intersection → refus) est testé et validé.

## 5. Vérifications complémentaires (hors DoD strict, à titre de contrôle qualité)

- `mypy src` → **Success: no issues found in 9 source files**.
- `ruff check .` → 7 avertissements de formatage d'imports (`I001`, non bloquants, aucune
  erreur logique). Non corrigés pour ne pas élargir le périmètre Phase 0 (le DoD ne requiert
  que `pytest` vert). Voir section « Points bloquants / remarques ».

## 6. Sécurité et secrets

- Recherche de motifs de secrets (clés API, tokens AWS, clés privées, mots de passe en dur)
  dans le code, la config et la documentation : **aucun résultat**.
- Seul `.env.example` est présent (aucun `.env` versionné).
- `.env.example` est complet : `APP_ENV`, `APP_NAME`, `LOG_LEVEL`, `DATABASE_URL`,
  `R2_*`, `IDENTITY_MODE`, `OIDC_*`, `CLAUDE_API_KEY`, `JEV_*`, `LOCAL_CORPUS_ALLOWED`,
  `MAX_LOCAL_SAMPLE_MB`.
- `.gitignore` couvre `.env`, caches, venv, dossiers de corpus/embeddings/vectorstore,
  clés/certificats et `secrets/`. Ajout effectué : `*.egg-info/` (artefact généré par
  l'installation éditable, non versionnable).

## 7. Definition of Done Phase 0 — état

| Critère | État |
|---|---|
| `pytest` passe | ✅ 5/5 |
| Aucun secret versionné | ✅ |
| `.env.example` complet | ✅ |
| Configuration DEV/UAT/PROD définie | ✅ (via `Settings.app_env`, `.env` par environnement) |
| Modèles métier de base définis | ✅ (`domain/models.py`) |
| ACL invariant testé | ✅ (`tests/test_acl.py`) |
| Taxonomie validée | ✅ (`config/document-taxonomy.yml` chargé et syntaxiquement valide) |
| Shortcuts enregistrés | ✅ (`shortcuts/registry.py`, 12 entrées, testé) |
| Rapport Phase 0 présent | ✅ (ce document) |

## 8. Points bloquants / remarques

Aucun point bloquant pour la Phase 0. Deux remarques mineures, non corrigées afin de ne pas
élargir le scope (aucun test ne les couvre, la DoD ne les exige pas) :

1. **Léger écart shortcuts vs config** : `config/shortcuts.yml` liste 11 raccourcis ;
   `src/rag_enterprise_lab/shortcuts/registry.py` en définit 12 (`/sources` en plus, absent
   du YAML). Les deux fichiers ne se désynchronisent pas au sens fonctionnel (le registre
   Python fait autorité côté code), mais une source unique de vérité pourrait être envisagée
   en Phase 1.
2. **Style d'imports** : `ruff check .` signale 7 avertissements `I001` (regroupement des
   imports) sur des fichiers d'adapters/config/tests. Purement cosmétique, aucun impact sur
   le comportement ni sur les tests.

Aucune des interdictions Phase 0 n'a été franchie : pas de génération des 5000 documents, pas
de base distante, pas de bucket R2, pas de clé API en dur, pas d'OCR, pas de frontend, aucun
échec de test masqué.

## 9. Commit

Dépôt git initialisé localement (`git init`) — aucun dépôt git n'existait auparavant.
Commit réalisé : `chore: bootstrap RAG Enterprise Lab architecture`.

---

**La Phase 0 est terminée et conforme à la Definition of Done. En attente de validation
explicite avant de démarrer la Phase 1.**
