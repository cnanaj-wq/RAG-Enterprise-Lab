# Use case 01 — Contract Signature Control

## Question
> Avons-nous toutes nos signatures de contrats pour le mois ?

## Faits calculés en SQL/règles métier
- expected_contracts
- signed_contracts
- pending_contracts
- blocked_contracts
- signature_rate
- secured_revenue
- pending_revenue
- at_risk_revenue

## Jev
Jev qualifie une situation à partir de faits déjà calculés.
Labels : COMPLETE, ON_TRACK, AT_RISK, BLOCKED.
Jev ne calcule pas le taux de signature.

## Raccourcis
/signatures mois
/signatures commerciaux
/signatures manquantes
/signatures risque
/signatures deadline 7j
/signatures client ACME
/cloture-commerciale
