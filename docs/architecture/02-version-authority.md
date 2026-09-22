# Document Authority & Version Resolution

Une date récente ne suffit pas à déterminer l'autorité.

Ordre d'autorité contractuelle configurable :
1. SIGNED_AMENDMENT
2. SIGNED_CONTRACT
3. SIGNED_PURCHASE_ORDER
4. APPROVED_PROPOSAL
5. APPROVED_PRICING_GRID
6. DRAFT

Le moteur conserve : version, status, valid_from, valid_to, supersedes,
signed_at, source_system, checksum.
Toute résolution doit être explicable et auditable.
