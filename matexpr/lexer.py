"""Analisador léxico.

Ignora espaços, tabulações, quebras de linha e comentários no estilo C
(/* ... */ e // ...). Reconhece:
  - num:     inteiros (42) e ponto flutuante (3.14)
  - id:      sequências de letras do alfabeto (a-z, A-Z)
  - type:    int, float
  - Matexpr: palavra reservada
  - símbolos: + - * / ( ) { } ;

Erros léxicos não interrompem a análise: são registrados em `errors` e o
léxico se recupera (descarta o caractere inválido, ou devolve o lexema mal
formado com o tipo mais provável) para que outros erros também sejam
encontrados.
"""

from .errors import LexicalError
from .tokens import KEYWORDS, SYMBOLS, Token, TokenType


def _is_letter(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.errors: list[LexicalError] = []

    # ---------- utilitários ----------

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _error(self, message: str, line: int) -> None:
        self.errors.append(LexicalError(message, line))

    # ---------- partes ignoradas ----------

    def _skip_ignored(self) -> None:
        """Pula espaços, tabulações, quebras de linha e comentários."""
        while True:
            ch = self._peek()
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                while self._peek() not in ("", "\n"):
                    self._advance()
            elif ch == "/" and self._peek(1) == "*":
                start_line = self.line
                self._advance()
                self._advance()
                while not (self._peek() == "*" and self._peek(1) == "/"):
                    if self._peek() == "":
                        self._error("comentário não fechado (falta '*/')", start_line)
                        return
                    self._advance()
                self._advance()
                self._advance()
            else:
                return

    # ---------- reconhecedores ----------

    def _number(self) -> Token:
        start, line = self.pos, self.line
        while _is_digit(self._peek()):
            self._advance()
        if self._peek() == ".":
            self._advance()
            if not _is_digit(self._peek()):
                self._error(
                    f"número mal formado '{self.source[start:self.pos]}' "
                    "(esperado dígito após o ponto)",
                    line,
                )
                return Token(TokenType.NUM, self.source[start:self.pos], line)
            while _is_digit(self._peek()):
                self._advance()
        if _is_letter(self._peek()) or self._peek() in ("_", "."):
            while _is_letter(self._peek()) or _is_digit(self._peek()) or self._peek() in ("_", "."):
                self._advance()
            self._error(f"número mal formado '{self.source[start:self.pos]}'", line)
        return Token(TokenType.NUM, self.source[start:self.pos], line)

    def _word(self) -> Token:
        start, line = self.pos, self.line
        while _is_letter(self._peek()):
            self._advance()
        if _is_digit(self._peek()) or self._peek() == "_":
            while _is_letter(self._peek()) or _is_digit(self._peek()) or self._peek() == "_":
                self._advance()
            self._error(
                f"identificador inválido '{self.source[start:self.pos]}' "
                "(identificadores devem conter apenas letras)",
                line,
            )
            return Token(TokenType.ID, self.source[start:self.pos], line)
        lexeme = self.source[start:self.pos]
        return Token(KEYWORDS.get(lexeme, TokenType.ID), lexeme, line)

    # ---------- interface pública ----------

    def next_token(self) -> Token:
        while True:
            self._skip_ignored()
            ch = self._peek()
            if ch == "":
                return Token(TokenType.EOF, "", self.line)
            if _is_digit(ch):
                return self._number()
            if _is_letter(ch):
                return self._word()
            if ch in SYMBOLS:
                line = self.line
                self._advance()
                return Token(SYMBOLS[ch], ch, line)
            self._error(f"caractere inválido '{ch}'", self.line)
            self._advance()  # descarta o caractere e tenta de novo

    def tokenize(self) -> list[Token]:
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type is TokenType.EOF:
                return tokens
