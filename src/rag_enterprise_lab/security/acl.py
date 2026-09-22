from rag_enterprise_lab.domain.models import AccessDecision, DocumentRecord, UserContext

RESTRICTED_MESSAGE = (
    "🔒 Cette information appartient à une catégorie documentaire restreinte "
    "à laquelle votre profil n'a pas accès."
)

def authorize(user: UserContext, document: DocumentRecord) -> AccessDecision:
    allowed = set(document.allowed_groups)
    user_groups = set(user.groups)
    matches = sorted(allowed.intersection(user_groups))

    if not allowed:
        return AccessDecision(allowed=False, reason="NO_ACL_DEFINED", matched_groups=[])

    if matches:
        return AccessDecision(allowed=True, reason="ACL_GROUP_MATCH", matched_groups=matches)

    return AccessDecision(allowed=False, reason="ACL_NO_MATCH", matched_groups=[])
