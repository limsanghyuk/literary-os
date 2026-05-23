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

# V607: SharedCharacterDB v2.0 + SharedWorldDB v2.0
from .shared_character_db_v2 import (
    CharacterSnapshot,
    ConflictRecord,
    RewardTrace,
    SharedCharacterDBV2,
)
from .shared_world_db_v2 import (
    LocationConflict,
    SharedWorldDBV2,
    WorldSnapshot,
)

__all__ += [
    # V607 — SharedCharacterDB v2.0
    "CharacterSnapshot", "RewardTrace", "ConflictRecord", "SharedCharacterDBV2",
    # V607 — SharedWorldDB v2.0
    "WorldSnapshot", "LocationConflict", "SharedWorldDBV2",
]

# V608: MultiWorkOrchestratorV2
from .multi_work_orchestrator_v2 import (
    InterProjectConflictReport,
    MultiWorkOrchestratorV2,
    ProjectCheckpoint,
)

__all__ += [
    # V608 — MultiWorkOrchestratorV2
    "ProjectCheckpoint", "InterProjectConflictReport", "MultiWorkOrchestratorV2",
]

# V609: MultiWorkCIMV2
from .multi_work_cim_v2 import (
    CIMEntryV2,
    CIMSnapshot,
    InterProjectCIMScore,
    MultiWorkCIMV2,
    ProjectCIMV2,
)

__all__ += [
    # V609 — MultiWorkCIMV2
    "CIMEntryV2", "ProjectCIMV2", "CIMSnapshot",
    "InterProjectCIMScore", "MultiWorkCIMV2",
]

# V610: MultiWorkCIM v2.0 팩토리 + 업그레이드 유틸리티
from .multi_work_cim import (  # noqa: E402
    CIMVersion,
    create_multi_work_cim,
    get_cim_version,
)

__all__ += [
    # V610 — MultiWorkCIM v2.0
    "CIMVersion", "create_multi_work_cim", "get_cim_version",
]
