from rag_enterprise_lab.domain.organization import DEPARTMENT_HEADCOUNT
from rag_enterprise_lab.identity.groups import DEPARTMENT_GROUPS, RAG_FINANCE, RAG_LEGAL


def test_exactly_120_employees(dataset):
    assert len(dataset.employees) == 120


def test_department_distribution_exact(dataset):
    counts: dict = {}
    for emp in dataset.employees:
        counts[emp.department] = counts.get(emp.department, 0) + 1
    assert counts == DEPARTMENT_HEADCOUNT


def test_no_duplicate_employee_id(dataset):
    ids = [e.employee_id for e in dataset.employees]
    assert len(ids) == len(set(ids))


def test_no_duplicate_email(dataset):
    emails = [e.corporate_email for e in dataset.employees]
    assert len(emails) == len(set(emails))


def test_all_manager_ids_valid(dataset):
    valid_ids = {e.employee_id for e in dataset.employees}
    managed = [e for e in dataset.employees if e.manager_id is not None]
    assert managed, "at least one employee must have a manager"
    assert all(e.manager_id in valid_ids for e in managed)


def test_no_hierarchy_cycle(dataset):
    by_id = {e.employee_id: e for e in dataset.employees}

    def has_cycle(start) -> bool:
        seen: set[str] = set()
        current = start
        while current.manager_id is not None:
            if current.manager_id in seen:
                return True
            seen.add(current.manager_id)
            current = by_id[current.manager_id]
        return False

    assert not any(has_cycle(e) for e in dataset.employees)

    top_level = [e for e in dataset.employees if e.manager_id is None]
    assert len(top_level) == 1, "exactly one root of the hierarchy (CEO) is expected"


def test_department_groups_coherent(dataset):
    for emp in dataset.employees:
        expected = DEPARTMENT_GROUPS[emp.department]
        if len(expected) > 1:
            # Finance / Legal : un des deux groupes spécialisés doit être présent.
            assert any(g in emp.security_groups for g in expected)
        else:
            assert expected[0] in emp.security_groups
        assert "RAG_ALL_EMPLOYEES" in emp.security_groups


def test_finance_legal_split_is_exhaustive(dataset):
    finance_legal = [e for e in dataset.employees if e.department.value == "Finance / Legal"]
    for emp in finance_legal:
        has_finance = RAG_FINANCE in emp.security_groups
        has_legal = RAG_LEGAL in emp.security_groups
        assert has_finance or has_legal
