# ADR-003 — Jev as bounded decision layer

Jev est utilisé derrière une interface applicative afin d'éviter le couplage au fournisseur.

Use : classification, intent routing, risk scoring, bounded decisions with confidence.

Exclusions : ACL decisions, irreversible GDPR deletion, deterministic financial calculations,
source-of-truth contract status.
