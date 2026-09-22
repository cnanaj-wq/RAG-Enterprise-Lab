from pydantic import BaseModel, Field

from rag_enterprise_lab.domain.models import AccessDecision
from rag_enterprise_lab.domain.organization import CLEARANCE_RANK, Clearance
from rag_enterprise_lab.security.acl import authorize_groups


class Resource(BaseModel):
    """Une ressource protégée générique (document, tableau de bord, dataset...).

    Le moteur reste déterministe et fondé sur des règles : Jev et Claude ne sont
    jamais consultés pour ALLOW/DENY (voir ADR-002).
    """

    resource_id: str
    resource_type: str
    allowed_groups: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    minimum_clearance: Clearance | None = None


def decide(
    *,
    user_groups: list[str],
    user_roles: list[str],
    user_clearance: Clearance,
    resource: Resource,
) -> AccessDecision:
    """Décision ALLOW/DENY déterministe, deny-by-default à chaque étage.

    Ordre d'évaluation : ACL (groupes) -> RBAC (rôles) -> ABAC (clearance).
    Le premier étage qui refuse arrête l'évaluation (fail closed).
    """
    acl_decision = authorize_groups(user_groups, resource.allowed_groups)
    if not acl_decision.allowed:
        return acl_decision

    if resource.required_roles and not (set(resource.required_roles) & set(user_roles)):
        return AccessDecision(
            allowed=False,
            reason="RBAC_ROLE_MISSING",
            matched_groups=acl_decision.matched_groups,
        )

    if (
        resource.minimum_clearance is not None
        and CLEARANCE_RANK[user_clearance] < CLEARANCE_RANK[resource.minimum_clearance]
    ):
        return AccessDecision(
            allowed=False,
            reason="ABAC_CLEARANCE_INSUFFICIENT",
            matched_groups=acl_decision.matched_groups,
        )

    return AccessDecision(
        allowed=True,
        reason="ACL_RBAC_ABAC_MATCH",
        matched_groups=acl_decision.matched_groups,
    )
