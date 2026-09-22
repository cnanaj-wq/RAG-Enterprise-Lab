def test_exactly_65_active_clients(dataset):
    assert len(dataset.clients) == 65
    assert all(c.status.value == "ACTIVE" for c in dataset.clients)


def test_exactly_120_prospects(dataset):
    assert len(dataset.prospects) == 120


def test_exactly_30_partners(dataset):
    assert len(dataset.partners) == 30


def test_exactly_80_suppliers(dataset):
    assert len(dataset.suppliers) == 80


def test_client_account_manager_valid(dataset):
    employee_ids = {e.employee_id for e in dataset.employees}
    for client in dataset.clients:
        assert client.account_manager_id in employee_ids
        assert client.sales_manager_id in employee_ids


def test_account_manager_in_sales(dataset):
    by_id = {e.employee_id: e for e in dataset.employees}
    for client in dataset.clients:
        account_manager = by_id[client.account_manager_id]
        assert account_manager.department.value == "Sales / Account"
        assert account_manager.job_title in ("Account Executive", "Key Account Manager")

        sales_manager = by_id[client.sales_manager_id]
        assert sales_manager.department.value == "Sales / Account"
        assert sales_manager.job_title == "Sales Manager"


def test_opportunity_per_active_client(dataset):
    client_ids = {c.customer_id for c in dataset.clients}
    opportunity_client_ids = {o.client_id for o in dataset.opportunities}
    assert opportunity_client_ids == client_ids
    assert len(dataset.opportunities) == len(dataset.clients)
