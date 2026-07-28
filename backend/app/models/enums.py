import enum


class UrlStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    redirect = "redirect"


class AuditStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class KeywordIntent(str, enum.Enum):
    informational = "informational"
    navigational = "navigational"
    transactional = "transactional"
    commercial = "commercial"


class KeywordPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
