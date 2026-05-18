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

from .multi_work_core import (
    WorkProject, WorkStatus, WorkSession, MultiWorkCore, ProjectConflict,
)
from .shared_character_db import (
    CharacterProfile, CharacterRelation, RelationType, SharedCharacterDB,
)
from .shared_world_db import (
    Location, Faction, TimelineEvent, LoreEntry, SharedWorldDB,
)
from .genre_transfer import (
    GenreProfile, TransferRecord, GenreTransferLearning,
)
from .project_isolation import (
    AccessType, DataScope, IsolationPolicy, IsolationViolation,
    AuditEntry, ProjectIsolationManager,
)
from .multi_work_cim import (
    CIMEntry, ProjectCIM, MultiWorkCIM,
)
from .author_license_api import (
    LicenseType, LicenseScope, LicenseViolation, AuthorLicense, AuthorLicenseAPI,
)
from .multi_work_orchestrator import (
    SceneProcessEvent, OrchestratorSnapshot, MultiWorkOrchestrator,
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
