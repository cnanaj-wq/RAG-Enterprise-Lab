# Modèle documentaire Phase 2

Le manifest (`data/seed/document_manifest.json`, 5000 entrées) décrit des
**métadonnées** — le contenu physique n'existe que pour ≤ 50 exemples
(`generation_status=EXAMPLE_GENERATED`). Le corpus complet sera généré
ultérieurement, directement vers Cloudflare R2.

## `DocumentManifestEntry` (`src/rag_enterprise_lab/domain/documents.py`)

| Champ | Type | Note |
|---|---|---|
| document_id | str | `DOC-00001`..`DOC-05000` |
| title | str | |
| document_type | str | voir taxonomie ci-dessous |
| domain | enum (7 valeurs) | |
| source_system | str | Workday / DocuSign / Salesforce / Confluence / SAP / SharePoint |
| owner | str | `employee_id` |
| classification | enum (6 valeurs, réutilise `domain/models.py::Classification`) | |
| version | str | `"1.0"`, `"2.0"`, ... (chronologique) |
| status | enum (7 valeurs, réutilise `domain/models.py::DocumentStatus`) | |
| valid_from / valid_to | date \| null | fenêtre de validité métier |
| created_at / approved_at / signed_at | datetime | approved/signed optionnels |
| supersedes | str \| null | `document_id` précédent |
| authority_level | enum (6 valeurs) | autorité légale — voir [version-resolution](../version-resolution/README.md) |
| related_customer_id / related_supplier_id / related_employee_id / related_project_id / related_opportunity_id / related_expected_contract_id | str \| null | toutes optionnelles |
| contains_personal_data | bool | |
| retention_policy | enum (5 valeurs) | |
| allowed_groups | list[str] | ACL — groupes Identity Phase 1 |
| checksum | str | **placeholder** (`sha256-placeholder-{document_id}`), pas un hash réel |
| storage_target | str | chemin R2 futur, ou `local://data/examples/...` pour les exemples |
| generation_status | enum (`NOT_GENERATED` / `EXAMPLE_GENERATED`) | |

## Taxonomie : 7 domaines, volumes exacts (5000 total)

| Domaine | Volume | Types de documents |
|---|---:|---|
| RH | 950 | EMPLOYMENT_CONTRACT, EMPLOYMENT_AMENDMENT, JOB_DESCRIPTION, HR_POLICY, COLLECTIVE_AGREEMENT, ONBOARDING_DOCUMENT, PAYROLL_RECORD |
| Legal / Contracts | 850 | CLIENT_CONTRACT, SUPPLIER_CONTRACT, PARTNER_CONTRACT, NDA, DPA, CONTRACT_AMENDMENT |
| Clients / Prospects | 900 | PROSPECT_FILE, CLIENT_DOSSIER, BUSINESS_CONTACT, TECHNICAL_CONTACT, COMPANY_REGISTRY_EXTRACT, INSURANCE_CERTIFICATE, SECURITY_APPENDIX |
| Pricing / Sales | 450 | PROPOSAL, PURCHASE_ORDER, PRICING_GRID, DISCOUNT_POLICY |
| IT / Architecture / Security | 850 | ARCHITECTURE, RUNBOOK, INCIDENT_REPORT, POSTMORTEM, API_DOCUMENTATION, SECURITY_POLICY |
| Projects / Procedures | 600 | PROJECT_CHARTER, PROJECT_STATUS_REPORT, PROCEDURE, DELIVERY_PLAN, MEETING_MINUTES |
| Finance / Compliance | 400 | INVOICE, BUDGET, FINANCE_POLICY, COMPLIANCE_REPORT |
| **Total** | **5000** | |

Source de vérité : `src/rag_enterprise_lab/domain/document_taxonomy.py`.

## Génération

`src/rag_enterprise_lab/generation/document_generator.py` produit une entrée
par domaine/type en cyclant sur les référentiels Phase 1 (employés, clients,
fournisseurs, projets, opportunités/contrats attendus) pour peupler les
`related_*`. `generation/version_chain_builder.py` construit ensuite les
chaînes `supersedes` (voir [version-resolution](../version-resolution/README.md)).

Aucun appel réseau, aucune écriture hors `data/seed/` et `data/examples/`.
