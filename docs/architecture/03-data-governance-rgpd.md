# Data Governance & RGPD

## Classification
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
PERSONAL_DATA
SENSITIVE_PERSONAL_DATA

## Métadonnées minimales
document_id, owner, source_system, classification, version, status,
valid_from, valid_to, ACL, retention policy, contains_personal_data,
checksum, ingestion timestamp.

## Suppression
document -> derived text -> chunks -> embeddings -> indexes -> audit event

La détection IA peut signaler ; la décision irréversible doit être gouvernée
par une règle ou une validation explicite.
