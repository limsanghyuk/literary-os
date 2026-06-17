# literary_system.quality — V447+ Quality Gate modules

from .quality_labels import QualityLabel, QualityTier, classify, make_label, DEMO_LABELS, summary  # V775
from .critic_discrimination_gate import g_critic_discrimination, DiscriminationResult, craft_axis_scorer, DISCRIMINATION_MIN  # V775
