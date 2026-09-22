from rag_enterprise_lab.domain.models import AccessDecision, DocumentRecord, UserContext

RESTRICTED_MESSAGE = (
    "🔒 Cette information appartient à une catégorie documentaire restreinte "
    "à laquelle votre profil n'a pas accès."
)

def authorize_groups(user_groups: list[str], allowed_groups: list[str]) -> AccessDecision:
    allowed = set(allowed_groups)
    groups = set(user_groups)
    matches = sorted(allowed.intersection(groups))

    if not allowed:
        return AccessDecision(allowed=False, reason="NO_ACL_DEFINED", matched_groups=[])

    if matches:
        return AccessDecision(allowed=True, reason="ACL_GROUP_MATCH", matched_groups=matches)

    return AccessDecision(allowed=False, reason="ACL_NO_MATCH", matched_groups=[])


def authorize(user: UserContext, document: DocumentRecord) -> AccessDecision:
    return authorize_groups(user.groups, document.allowed_groups)
