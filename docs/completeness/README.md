# Complétude documentaire

Règles chargées depuis `config/completeness/*.yml` par
`src/rag_enterprise_lab/domain/completeness.py::compute_completeness`.
Source de vérité unique — jamais dupliquée dans le code.

## Client Dossier (Phase 0, `config/completeness/client.yml`)

`CLIENT_CONTRACT`, `NDA`, `DPA`, `PURCHASE_ORDER`, `PRICING_GRID`,
`SECURITY_APPENDIX`, `INSURANCE_CERTIFICATE`, `COMPANY_REGISTRY_EXTRACT`,
`BUSINESS_CONTACT`, `TECHNICAL_CONTACT` (10 types).

## Supplier Dossier (Phase 2, `config/completeness/supplier.yml`)

`SUPPLIER_CONTRACT`, `NDA`, `DPA`, `INSURANCE_CERTIFICATE`,
`COMPANY_REGISTRY_EXTRACT`, `SECURITY_APPENDIX`, `BUSINESS_CONTACT`
(7 types).

## HR Employee Dossier (Phase 2, `config/completeness/hr_employee.yml`)

`EMPLOYMENT_CONTRACT`, `JOB_DESCRIPTION`, `ONBOARDING_DOCUMENT`,
`PAYROLL_RECORD` (4 types).

## Calcul

```python
compute_completeness(
    dossier_type="CLIENT",              # ou "SUPPLIER" / "HR_EMPLOYEE"
    related_id="CLI-0001",
    present_document_types={"CLIENT_CONTRACT", "NDA"},
)
# -> CompletenessResult(is_complete=False, missing_types=[...], completeness_ratio=0.2)
```

5 exemples de complétude client (dérivés du manifest généré) sont inclus
dans `data/seed/document_expected_answers.json`
(`category="COMPLETENESS_CLIENT_DOSSIER"`).
