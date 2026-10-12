"""
CAI-Lang Abstract Syntax Tree (AST) Nodes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class DirectiveNode:
    name: str                           # e.g., 'pace', 'visual_role', 'motion', 'impact'
    action: str                         # e.g., 'ken_burns', 'white_flash', 'MONEY_SHOT'
    args: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PhaseNode:
    name: str                           # 'INTRO', 'BUILDUP', 'FAKEOUT', 'DROP', 'GROOVE', 'OUTRO'
    start_sec: float
    end_sec: float
    directives: List[DirectiveNode] = field(default_factory=list)

@dataclass
class ProgramNode:
    track_title: str
    track_meta: Dict[str, Any] = field(default_factory=dict)
    phases: List[PhaseNode] = field(default_factory=list)
