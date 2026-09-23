# Quarantaine documentaire

## Principe

**Un document problématique n'est jamais supprimé silencieusement.** Le
contenu brut est copié vers `quarantine/{document_id}.{ext}` (préservé pour
investigation), le statut passe à `QUARANTINED`, et un événement d'audit est
émis avec la raison.

## Raisons (`domain/processing.py::QuarantineReason`)

| Raison | Déclencheur |
|---|---|
| `PARSING_ERROR` | Erreur inattendue levée par le parseur Docling |
| `OCR_LOW_CONFIDENCE` | Signal de confiance OCR faible (worker Docling réel) |
| `UNSUPPORTED_FORMAT` | Extension hors des 7 formats supportés |
| `CORRUPTED_FILE` | Contenu vide, texte non décodable, binaire trop petit |
| `METADATA_MISMATCH` | `document_id` parsé ≠ `document_id` attendu |
| `CHECKSUM_MISMATCH` | SHA-256 du contenu téléchargé ≠ checksum stocké (`head()`) |

## Routing (`ingestion/pipeline.py::ingest` / `_quarantine`)

1. Téléchargement du raw object.
2. Vérification checksum → `CHECKSUM_MISMATCH` si divergence.
3. `parser.parse(...)` :
   - `UnsupportedFormatError` → `UNSUPPORTED_FORMAT` ;
   - `CorruptedDocumentError` → `CORRUPTED_FILE` ;
   - toute autre exception → `PARSING_ERROR`.
4. Cohérence des métadonnées parsées → `METADATA_MISMATCH` si divergence.

Chaque cas est testé indépendamment
(`tests/test_ingestion_pipeline.py::test_ingest_quarantine*`,
`test_ingest_checksum_mismatch_triggers_quarantine`).

## Ce que la quarantaine ne fait jamais

- Elle ne supprime jamais l'objet `raw/` d'origine.
- Elle n'écrase jamais un objet existant sans le signaler (voir
  idempotence / CONFLICT dans [docs/ingestion](../ingestion/README.md)).
- Elle ne bloque pas le reste du run : les autres documents continuent
  d'être traités.
