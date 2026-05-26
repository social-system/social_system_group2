DEFAULT_ALIAS_SOURCE = "user_confirmed"

AUTO_RESOLVE_ALIAS_SOURCES = frozenset(
    {"user_confirmed", "seed", "admin"}
)
CANDIDATE_ALIAS_SOURCES = AUTO_RESOLVE_ALIAS_SOURCES | frozenset(
    {"ocr_suggested"}
)
ALLOWED_ALIAS_SOURCES = CANDIDATE_ALIAS_SOURCES
