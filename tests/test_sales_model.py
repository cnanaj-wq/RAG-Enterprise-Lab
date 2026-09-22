"""Correctif ciblé demandé avant la Phase 2 : Opportunity, ExpectedContract et
signature_status doivent être des informations distinctes et non ambiguës."""

from rag_enterprise_lab.domain.sales import ExpectedContract, Opportunity, SignatureStatus


def test_signature_status_lives_only_on_expected_contract():
    assert "signature_status" not in Opportunity.model_fields
    assert "signature_status" in ExpectedContract.model_fields


def test_expected_contract_is_explicit_and_linked_to_its_opportunity(dataset):
    assert len(dataset.expected_contracts) == len(dataset.opportunities)
    opportunities_by_id = {o.opportunity_id: o for o in dataset.opportunities}

    for contract in dataset.expected_contracts:
        opportunity = opportunities_by_id[contract.opportunity_id]

        # Les 7 facettes demandées doivent être séparément accessibles :
        assert contract.opportunity_id == opportunity.opportunity_id  # l'opportunité
        assert contract.expected_contract_id  # le contrat attendu (identité propre)
        assert contract.sales_owner_id == opportunity.sales_owner_id  # le propriétaire commercial
        assert contract.client_id == opportunity.client_id  # le client
        assert contract.expected_close_date == opportunity.expected_close_date
        assert contract.expected_amount == opportunity.expected_amount
        assert contract.signature_status in SignatureStatus


def test_opportunity_stage_is_derived_from_signature_status(dataset):
    contracts_by_opportunity = {c.opportunity_id: c for c in dataset.expected_contracts}
    for opportunity in dataset.opportunities:
        contract = contracts_by_opportunity[opportunity.opportunity_id]
        if contract.signature_status == SignatureStatus.SIGNED:
            assert opportunity.stage.value == "WON"
        elif contract.signature_status in (SignatureStatus.DECLINED, SignatureStatus.BLOCKED):
            assert opportunity.stage.value == "LOST"
        else:
            assert opportunity.stage.value == "OPEN"


def test_no_duplicate_expected_contract_id(dataset):
    ids = [c.expected_contract_id for c in dataset.expected_contracts]
    assert len(ids) == len(set(ids))
