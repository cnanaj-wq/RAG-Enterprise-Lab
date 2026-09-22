from rag_enterprise_lab.domain.models import Classification, DocumentRecord, DocumentStatus, UserContext
from rag_enterprise_lab.security.acl import authorize

def _doc(groups: list[str]) -> DocumentRecord:
    return DocumentRecord(
        document_id="DOC-001",
        title="Salary file",
        document_type="HR",
        version="1.0",
        status=DocumentStatus.APPROVED,
        owner="HR",
        classification=Classification.RESTRICTED,
        source_system="R2",
        allowed_groups=groups,
    )

def test_access_allowed_on_group_match():
    user = UserContext(user_id="EMP-047", groups=["RAG_HR"])
    decision = authorize(user, _doc(["RAG_HR", "RAG_EXECUTIVE"]))
    assert decision.allowed is True
    assert decision.reason == "ACL_GROUP_MATCH"

def test_access_denied_without_group_match():
    user = UserContext(user_id="EMP-047", groups=["RAG_DATA_AI"])
    decision = authorize(user, _doc(["RAG_HR", "RAG_EXECUTIVE"]))
    assert decision.allowed is False
    assert decision.reason == "ACL_NO_MATCH"

def test_access_denied_when_acl_missing():
    user = UserContext(user_id="EMP-047", groups=["RAG_ALL_EMPLOYEES"])
    decision = authorize(user, _doc([]))
    assert decision.allowed is False
    assert decision.reason == "NO_ACL_DEFINED"
