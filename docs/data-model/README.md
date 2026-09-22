# Modèle de données Phase 1

Toutes les entités sont des modèles Pydantic v2 (`src/rag_enterprise_lab/domain/`),
sérialisées en JSON déterministe dans `data/seed/`.

## Employee (`domain/organization.py`)

| Champ | Type |
|---|---|
| employee_id | str (`EMP-0001`..`EMP-0120`) |
| first_name, last_name | str (fictifs) |
| corporate_email | str (`prenom.nom@genai-enterprise-lab.example`) |
| department | enum (9 valeurs) |
| business_unit | enum (`Corporate` / `Go-To-Market` / `Delivery`) |
| job_title | str |
| manager_id | str \| null |
| location | str |
| employment_type | enum (`CDI` / `CDD` / `FREELANCE` / `APPRENTICESHIP`) |
| seniority_level | enum (`JUNIOR`..`EXECUTIVE`) |
| active | bool |
| security_groups | list[str] (ACL) |
| identity_roles | list[str] (RBAC) |
| clearance | enum (ABAC) |
| project_memberships | list[project_id] |
| client_memberships | list[customer_id] |

## Client / Prospect / Partner / Supplier (`domain/commercial.py`)

- **Client** : `customer_id`, `client_code`, `name`, `industry`, `segment`,
  `account_manager_id`, `sales_manager_id`, `status`, `risk_level`,
  `creation_date`.
- **Prospect** : `prospect_id`, `name`, `industry`, `segment`, `owner_id`,
  `status`, `creation_date`.
- **Partner** : `partner_id`, `name`, `partner_type`, `country`,
  `creation_date`.
- **Supplier** : `supplier_id`, `name`, `category`, `country`, `criticality`,
  `creation_date`.

## Project (`domain/delivery.py`)

`project_id`, `project_code`, `name`, `client_id`, `status`,
`delivery_lead_id`, `team_member_ids`, `start_date`. Un projet par client
actif (65), équipe de 2 à 4 membres piochés dans Consulting / Data & AI /
Engineering.

## Opportunity (`domain/sales.py`)

Support direct du scénario *"avons-nous toutes nos signatures de contrats du
mois ?"* (voir [01-contract-signature-control.md](../architecture/01-contract-signature-control.md)) :
`opportunity_id`, `client_id`, `sales_owner_id`, `expected_close_date`,
`expected_amount`, `signature_status`, `created_date`.

`signature_status` (7 valeurs exactes) :
`NOT_SENT → SENT → VIEWED → PARTIALLY_SIGNED → SIGNED` ; branches d'échec :
`DECLINED`, `BLOCKED`.

## Relations

```
Employee (manager_id) --------> Employee            [hiérarchie]
Employee (security_groups) ---> Identity groups      [ACL]
Client (account_manager_id) --> Employee (Sales)     [1:1]
Client (sales_manager_id) ----> Employee (Sales)     [1:1]
Project (client_id) ----------> Client               [1:1]
Project (team_member_ids) ----> Employee[]           [N:N]
Opportunity (client_id) ------> Client                [1:1, 1 opportunité / client actif]
Opportunity (sales_owner_id) -> Employee (Sales)      [1:1]
```

## Fichiers générés (`data/seed/`)

`employees.json`, `clients.json`, `prospects.json`, `partners.json`,
`suppliers.json`, `projects.json`, `opportunities.json`,
`identity_groups.json`, `manifest.json` (seed, compte par entité).
