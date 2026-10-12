"""
CAI-Lang Token Definitions
Domain-Specific Language for Audio-Visual Choreography
"""

from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    TRACK = auto()
    CHOREOGRAPHY = auto()
    PHASE = auto()
    INTRO = auto()
    BUILDUP = auto()
    FAKEOUT = auto()
    DROP = auto()
    GROOVE = auto()
    OUTRO = auto()
    
    # Properties & Directives
    PACE = auto()
    VISUAL_ROLE = auto()
    MOTION = auto()
    COLOR = auto()
    IMPACT = auto()
    FX = auto()
    SYNC = auto()
    
    # Roles
    MONEY_SHOT = auto()
    ATMOSPHERIC = auto()
    DETAIL_TEASE = auto()
    ACTION_FLOW = auto()

    # Literals & Identifiers
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    TIME_SEC = auto()         # e.g., 5.88s

    # Symbols
    LBRACE = auto()           # {
    RBRACE = auto()           # }
    LBRACKET = auto()         # [
    RBRACKET = auto()         # ]
    LPAREN = auto()           # (
    RPAREN = auto()           # )
    COLON = auto()            # :
    SEMICOLON = auto()        # ;
    COMMA = auto()            # ,
    ARROW = auto()            # ->
    EOF = auto()

class Token:
    def __init__(self, token_type: TokenType, value: any, line: int):
        self.type = token_type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line})"
