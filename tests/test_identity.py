from rag_enterprise_lab.domain.organization import Clearance
from rag_enterprise_lab.identity.groups import (
    RAG_ALL_EMPLOYEES,
    RAG_EXECUTIVE,
    STATIC_GROUPS,
    client_group,
    project_group,
)
from rag_enterprise_lab.security.authorization import Resource, decide


def test_static_groups_present(dataset):
    for group in STATIC_GROUPS:
        assert group in dataset.identity_groups


def test_dynamic_client_and_project_groups_materialized(dataset):
    for client in dataset.clients:
        assert client_group(client.client_code) in dataset.identity_groups
    for project in dataset.projects:
        assert project_group(project.project_code) in dataset.identity_groups


def test_acl_deny_by_default_no_allowed_groups(dataset):
    resource = Resource(resource_id="R-EMPTY", resource_type="document", allowed_groups=[])
    for emp in dataset.employees[:10]:
        decision = decide(
            user_groups=emp.security_groups,
            user_roles=emp.identity_roles,
            user_clearance=emp.clearance,
            resource=resource,
        )
        assert decision.allowed is False
        assert decision.reason == "NO_ACL_DEFINED"


def test_acl_deny_by_default_no_group_overlap(dataset):
    resource = Resource(
        resource_id="R-EXEC",
        resource_type="document",
        allowed_groups=[RAG_EXECUTIVE],
    )
    non_executives = [e for e in dataset.employees if RAG_EXECUTIVE not in e.security_groups]
    assert non_executives
    for emp in non_executives[:15]:
        decision = decide(
            user_groups=emp.security_groups,
            user_roles=emp.identity_roles,
            user_clearance=emp.clearance,
            resource=resource,
        )
        assert decision.allowed is False
        assert decision.reason == "ACL_NO_MATCH"


def test_acl_allows_on_group_match(dataset):
    executives = [e for e in dataset.employees if RAG_EXECUTIVE in e.security_groups]
    assert executives
    resource = Resource(
        resource_id="R-EXEC",
        resource_type="document",
        allowed_groups=[RAG_EXECUTIVE],
    )
    decision = decide(
        user_groups=executives[0].security_groups,
        user_roles=executives[0].identity_roles,
        user_clearance=executives[0].clearance,
        resource=resource,
    )
    assert decision.allowed is True


def test_abac_clearance_denies_when_insufficient(dataset):
    standard_employee = next(e for e in dataset.employees if e.clearance == Clearance.STANDARD)
    resource = Resource(
        resource_id="R-SENSITIVE",
        resource_type="document",
        allowed_groups=[RAG_ALL_EMPLOYEES],
        minimum_clearance=Clearance.EXECUTIVE,
    )
    decision = decide(
        user_groups=standard_employee.security_groups,
        user_roles=standard_employee.identity_roles,
        user_clearance=standard_employee.clearance,
        resource=resource,
    )
    assert decision.allowed is False
    assert decision.reason == "ABAC_CLEARANCE_INSUFFICIENT"


def test_jev_and_claude_are_never_authorization_dependencies():
    import ast

    import rag_enterprise_lab.security.authorization as module

    with open(module.__file__, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())

    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not any("jev" in name.lower() for name in imported_modules)
    assert not any("claude" in name.lower() for name in imported_modules)
