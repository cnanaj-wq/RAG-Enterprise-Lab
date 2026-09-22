# ADR-002 — Authorization before LLM

## Decision
Le LLM ne décide jamais des droits d'accès.

## Required flow
Identity -> Policy -> ACL filter -> Retrieval -> Reranking -> LLM

## Denial message
🔒 Cette information appartient à une catégorie documentaire restreinte à laquelle votre profil n'a pas accès.
