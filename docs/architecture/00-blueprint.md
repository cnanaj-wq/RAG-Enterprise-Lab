# Architecture Blueprint

## Principe directeur
La bonne information, dans la bonne version, pour la bonne personne, avec une source vérifiable.

## Flux documentaire
R2 EU -> Remote Docling Worker -> normalization -> metadata/classification ->
PostgreSQL registry -> chunking/embedding -> pgvector

## Flux question
User -> Identity claims -> intent routing -> ACL/RBAC/ABAC policy ->
hybrid retrieval -> version resolver -> reranker / decision gate -> Claude -> answer + citations

## Règle sécurité
Un contenu interdit ne doit jamais être fourni au LLM.

## Recherche hybride
- vector similarity
- full text search
- SQL metadata filters
- ACL filters
- version/status filters
- reranking

## Jev
Autorisés : classification, routing, risk scoring, anomaly candidate, bounded typed decision.
Interdits : authorization, final GDPR deletion, legal authority resolution without deterministic rules.
