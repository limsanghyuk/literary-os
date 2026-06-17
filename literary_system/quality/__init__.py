# literary_system.quality — V447+ Quality Gate modules

from .quality_labels import QualityLabel, QualityTier, classify, make_label, DEMO_LABELS, summary  # V775
from .critic_discrimination_gate import g_critic_discrimination, DiscriminationResult, craft_axis_scorer, DISCRIMINATION_MIN  # V775

from .quality_aggregator import (AggInput, aggregate, build_labels, from_drama_dict, label_summary, commercial_from_viewership, craft_from_expert)  # V776
