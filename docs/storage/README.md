# Stockage cloud — Cloudflare R2 (S3-compatible)

## Principe

Le corpus complet ne doit **jamais** être conservé durablement sur le poste
utilisateur. Seuls existent localement : le code, les tests, les schémas, et
au maximum 50 documents exemples (`data/examples/`, issus de la Phase 2).

## Configuration — jamais de credential en dur

Exclusivement via variables d'environnement (`core/config.py::Settings`,
déjà déclarées dans `.env.example` depuis la Phase 0) :

```
R2_ENDPOINT
R2_BUCKET
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
```

`adapters/r2.py::credentials_available(settings)` vérifie leur présence
avant toute tentative de connexion. Si elles sont absentes,
`R2StorageAdapter.__init__` refuse de s'instancier
(`RuntimeError: ... BLOCKED_BY_CREDENTIALS`) — aucune ressource distante
n'est jamais créée ni supposée exister.

## Adapter (`adapters/r2.py`)

- `ObjectStorePort` (Protocol) : `put_bytes`, `get_bytes`, `head`, `delete`.
- `InMemoryObjectStore` : mock déterministe sans réseau, utilisé par tous
  les tests unitaires et le mode offline.
- `R2StorageAdapter` : implémentation réelle via `boto3` (client S3 pointé
  sur `R2_ENDPOINT`). `head()` lit un checksum stocké en métadonnée S3
  personnalisée (`Metadata={"checksum": ...}`), utilisé pour l'idempotence.

## Bucket layout (`storage/bucket_layout.py`)

```
raw/{hr,legal,clients,pricing,technical,projects,finance}/{document_id}.{ext}
processed/{document_id}/{document.json,content.md,metadata.json,tables.json?}
quarantine/{document_id}.{ext}
archive/{document_id}.{ext}
manifests/{filename}
```

Les 7 sous-dossiers `raw/` correspondent aux 7 domaines Phase 2
(`RAG_DOMAIN_FOLDER`), avec un nommage court dédié (`technical` pour
*IT / Architecture / Security*, etc.).

## Région / juridiction EU

`R2_ENDPOINT` est fourni par le compte Cloudflare et détermine déjà la
juridiction du bucket (R2 EU jurisdictional restriction côté Cloudflare).
Aucun bucket n'a été créé dans cette phase (voir § Provisioning distant du
rapport) — la contrainte EU est documentée ici pour la provisioning future.

## Provisioning distant — état actuel

**BLOCKED_BY_CREDENTIALS.** Aucun `.env` ni variable d'environnement R2
n'est configuré dans cet environnement. Voir
`docs/phase-reports/PHASE-3-REPORT.md` § Checklist pour la marche à suivre.
