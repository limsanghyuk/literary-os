"""
literary_system.multiwork — Stage C MultiWorkOrchestrator
V562: MultiWorkCore
V563: SharedCharacterDB
V564: SharedWorldDB
V565: GenreTransferLearning
V566: ProjectIsolation
V567: MultiWorkCIM
V568: AuthorLicenseAPI
V570: MultiWorkOrchestrator
"""

from .author_license_api import (
    AuthorLicense,
    AuthorLicenseAPI,
    LicenseScope,
    LicenseType,
    LicenseViolation,
)
from .genre_transfer import (
    GenreProfile,
    GenreTransferLearning,
    TransferRecord,
)
from .multi_work_cim import (
    CIMEntry,
    MultiWorkCIM,
    ProjectCIM,
)
from .multi_work_core import (
    MultiWorkCore,
    ProjectConflict,
    WorkProject,
    WorkSession,
    WorkStatus,
)
from .multi_work_orchestrator import (
    MultiWorkOrchestrator,
    OrchestratorSnapshot,
    SceneProcessEvent,
)
from .project_isolation import (
    AccessType,
    AuditEntry,
    DataScope,
    IsolationPolicy,
    IsolationViolation,
    ProjectIsolationManager,
)
from .shared_character_db import (
    CharacterProfile,
    CharacterRelation,
    RelationType,
    SharedCharacterDB,
)
from .shared_world_db import (
    Faction,
    Location,
    LoreEntry,
    SharedWorldDB,
    TimelineEvent,
)

__all__ = [
    # V562
    "WorkProject", "WorkStatus", "WorkSession", "MultiWorkCore", "ProjectConflict",
    # V563
    "CharacterProfile", "CharacterRelation", "RelationType", "SharedCharacterDB",
    # V564
    "Location", "Faction", "TimelineEvent", "LoreEntry", "SharedWorldDB",
    # V565
    "GenreProfile", "TransferRecord", "GenreTransferLearning",
    # V566
    "AccessType", "DataScope", "IsolationPolicy", "IsolationViolation",
    "AuditEntry", "ProjectIsolationManager",
    # V567
    "CIMEntry", "ProjectCIM", "MultiWorkCIM",
    # V568
    "LicenseType", "LicenseScope", "LicenseViolation", "AuthorLicense", "AuthorLicenseAPI",
    # V570
    "SceneProcessEvent", "OrchestratorSnapshot", "MultiWorkOrchestrator",
]
