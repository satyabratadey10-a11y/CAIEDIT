"""
CAI-Lang Lexer (Lexical Analyzer)
Converts CAI-Lang script source code into a stream of tokens.
"""

from typing import List
from caiedit.cailang.tokens import TokenType, Token

KEYWORDS = {
    "track": TokenType.TRACK,
    "choreography": TokenType.CHOREOGRAPHY,
    "phase": TokenType.PHASE,
    "INTRO": TokenType.INTRO,
    "BUILDUP": TokenType.BUILDUP,
    "FAKEOUT": TokenType.FAKEOUT,
    "DROP": TokenType.DROP,
    "GROOVE": TokenType.GROOVE,
    "OUTRO": TokenType.OUTRO,
    "pace": TokenType.PACE,
    "visual_role": TokenType.VISUAL_ROLE,
    "motion": TokenType.MOTION,
    "color": TokenType.COLOR,
    "impact": TokenType.IMPACT,
    "fx": TokenType.FX,
    "sync": TokenType.SYNC,
    "MONEY_SHOT": TokenType.MONEY_SHOT,
    "ATMOSPHERIC": TokenType.ATMOSPHERIC,
    "DETAIL_TEASE": TokenType.DETAIL_TEASE,
    "ACTION_FLOW": TokenType.ACTION_FLOW,
}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < self.length:
            ch = self.source[self.pos]

            # Whitespace & line count
            if ch == '\n':
                self.line += 1
                self.pos += 1
                continue
            elif ch.isspace():
                self.pos += 1
                continue

            # Comments (# or //)
            if ch == '#' or (ch == '/' and self.peek() == '/'):
                while self.pos < self.length and self.source[self.pos] != '\n':
                    self.pos += 1
                continue

            # Symbols
            if ch == '{':
                tokens.append(Token(TokenType.LBRACE, '{', self.line))
                self.pos += 1
            elif ch == '}':
                tokens.append(Token(TokenType.RBRACE, '}', self.line))
                self.pos += 1
            elif ch == '[':
                tokens.append(Token(TokenType.LBRACKET, '[', self.line))
                self.pos += 1
            elif ch == ']':
                tokens.append(Token(TokenType.RBRACKET, ']', self.line))
                self.pos += 1
            elif ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.line))
                self.pos += 1
            elif ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.line))
                self.pos += 1
            elif ch == ':':
                tokens.append(Token(TokenType.COLON, ':', self.line))
                self.pos += 1
            elif ch == ';':
                tokens.append(Token(TokenType.SEMICOLON, ';', self.line))
                self.pos += 1
            elif ch == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.line))
                self.pos += 1
            elif ch == '-' and self.peek() == '>':
                tokens.append(Token(TokenType.ARROW, '->', self.line))
                self.pos += 2
            # Strings
            elif ch == '"' or ch == "'":
                tokens.append(self._read_string(ch))
            # Numbers / Time (e.g., 5.88s or 60)
            elif ch.isdigit() or (ch == '.' and self.peek().isdigit()):
                tokens.append(self._read_number())
            # Identifiers & Keywords
            elif ch.isalpha() or ch == '_':
                tokens.append(self._read_identifier())
            else:
                self.pos += 1

        tokens.append(Token(TokenType.EOF, None, self.line))
        return tokens

    def peek(self) -> str:
        if self.pos + 1 < self.length:
            return self.source[self.pos + 1]
        return ''

    def _read_string(self, quote: str) -> Token:
        start_line = self.line
        self.pos += 1
        start = self.pos
        while self.pos < self.length and self.source[self.pos] != quote:
            if self.source[self.pos] == '\n':
                self.line += 1
            self.pos += 1
        val = self.source[start:self.pos]
        if self.pos < self.length:
            self.pos += 1
        return Token(TokenType.STRING, val, start_line)

    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < self.length and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            self.pos += 1

        # Check for time suffix 's' (e.g. 5.88s)
        if self.pos < self.length and self.source[self.pos] == 's':
            num_str = self.source[start:self.pos]
            self.pos += 1
            return Token(TokenType.TIME_SEC, float(num_str), self.line)

        num_str = self.source[start:self.pos]
        val = float(num_str) if '.' in num_str else int(num_str)
        return Token(TokenType.NUMBER, val, self.line)

    def _read_identifier(self) -> Token:
        start = self.pos
        while self.pos < self.length and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        word = self.source[start:self.pos]
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word, self.line)
