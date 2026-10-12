"""
CAI-Lang Parser
Constructs an Abstract Syntax Tree (AST) from token stream.
"""

from typing import List, Dict, Any
from caiedit.cailang.tokens import TokenType, Token
from caiedit.cailang.ast_nodes import ProgramNode, PhaseNode, DirectiveNode

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[0] if tokens else None

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = None

    def match(self, token_type: TokenType) -> bool:
        if self.current and self.current.type == token_type:
            self.advance()
            return True
        return False

    def expect(self, token_type: TokenType) -> Token:
        if self.current and self.current.type == token_type:
            tok = self.current
            self.advance()
            return tok
        curr_name = self.current.type.name if self.current else "EOF"
        raise SyntaxError(f"Expected {token_type.name} at line {getattr(self.current, 'line', 0)}, got {curr_name}")

    def parse(self) -> ProgramNode:
        title = "Untitled"
        meta = {}
        phases = []

        while self.current and self.current.type != TokenType.EOF:
            if self.match(TokenType.TRACK):
                title_tok = self.expect(TokenType.STRING)
                title = title_tok.value
                if self.match(TokenType.LBRACE):
                    while self.current and self.current.type != TokenType.RBRACE:
                        key = self.expect(TokenType.IDENTIFIER).value
                        self.expect(TokenType.COLON)
                        val = self.current.value
                        self.advance()
                        self.match(TokenType.SEMICOLON)
                        meta[key] = val
                    self.expect(TokenType.RBRACE)

            elif self.match(TokenType.CHOREOGRAPHY):
                self.expect(TokenType.LBRACE)
                while self.current and self.current.type != TokenType.RBRACE:
                    if self.match(TokenType.PHASE):
                        phases.append(self._parse_phase())
                    else:
                        self.advance()
                self.expect(TokenType.RBRACE)

            elif self.match(TokenType.PHASE):
                phases.append(self._parse_phase())
            else:
                self.advance()

        return ProgramNode(track_title=title, track_meta=meta, phases=phases)

    def _parse_phase(self) -> PhaseNode:
        # Phase name
        name_tok = self.current
        self.advance()
        name = name_tok.value

        # Time range [start -> end]
        start_sec = 0.0
        end_sec = 10.0
        if self.match(TokenType.LBRACKET):
            start_tok = self.current
            start_sec = float(start_tok.value)
            self.advance()
            self.expect(TokenType.ARROW)
            end_tok = self.current
            end_sec = float(end_tok.value)
            self.advance()
            self.expect(TokenType.RBRACKET)

        # Body
        directives = []
        self.expect(TokenType.LBRACE)
        while self.current and self.current.type != TokenType.RBRACE:
            directive = self._parse_directive()
            directives.append(directive)
            self.match(TokenType.SEMICOLON)
        self.expect(TokenType.RBRACE)

        return PhaseNode(name=name, start_sec=start_sec, end_sec=end_sec, directives=directives)

    def _parse_directive(self) -> DirectiveNode:
        dir_name = self.current.value
        self.advance()
        self.expect(TokenType.COLON)

        action_name = self.current.value
        self.advance()

        args = {}
        # Parse optional function args (key: val, ...)
        if self.match(TokenType.LPAREN):
            while self.current and self.current.type != TokenType.RPAREN:
                arg_key = self.current.value
                self.advance()
                self.expect(TokenType.COLON)
                arg_val = self.current.value
                self.advance()
                args[arg_key] = arg_val
                self.match(TokenType.COMMA)
            self.expect(TokenType.RPAREN)

        return DirectiveNode(name=dir_name, action=action_name, args=args)
