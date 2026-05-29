"""literary_system.trajectory — 궤적 + 궤적 패밀리."""
# V11.39.0 ADR-128: trajectory_family/ 연결
try:
    from literary_system.trajectory_family.trajectory_family_interpolator import (
        TrajectoryFamilyMatcher,
        TrajectoryFamilyProfile,
        TrajectoryFamilyRegistry,
    )
except ImportError:
    TrajectoryFamilyMatcher = None
    TrajectoryFamilyProfile = None
    TrajectoryFamilyRegistry = None
