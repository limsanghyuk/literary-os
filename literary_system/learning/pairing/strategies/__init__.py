from .base import (BaseStrategy, RawPair, PairVerdict, MIX, OVERGEN,
                   allocate, process_candidate)
from .p1 import P1GradedDegradation
from .p3 import P3AntiLLM
from .p2 import P2OnPolicy
from .p4 import P4Ties

STRATEGIES = {s.name: s for s in
              (P1GradedDegradation(), P3AntiLLM(), P2OnPolicy(), P4Ties())}

__all__ = ["BaseStrategy", "RawPair", "PairVerdict", "MIX", "OVERGEN",
           "allocate", "process_candidate", "STRATEGIES",
           "P1GradedDegradation", "P3AntiLLM", "P2OnPolicy", "P4Ties"]
