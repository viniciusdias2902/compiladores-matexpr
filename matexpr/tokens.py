"""Definição dos tokens produzidos pelo analisador léxico."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    MATEXPR = auto()   # palavra reservada "Matexpr"
    TYPE = auto()      # "int" ou "float"
    ID = auto()        # nome de variável (somente letras)
    NUM = auto()       # número inteiro ou ponto flutuante
    PLUS = auto()      # +
    MINUS = auto()     # -
    TIMES = auto()     # *
    DIVIDE = auto()    # /
    LPAREN = auto()    # (
    RPAREN = auto()    # )
    LBRACE = auto()    # {
    RBRACE = auto()    # }
    SEMI = auto()      # ;
    EOF = auto()       # fim do arquivo


KEYWORDS = {
    "Matexpr": TokenType.MATEXPR,
    "int": TokenType.TYPE,
    "float": TokenType.TYPE,
}

SYMBOLS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.TIMES,
    "/": TokenType.DIVIDE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ";": TokenType.SEMI,
}

# Descrição legível de cada tipo, usada nas mensagens de erro.
DESCRIPTIONS = {
    TokenType.MATEXPR: "'Matexpr'",
    TokenType.TYPE: "tipo (int ou float)",
    TokenType.ID: "identificador",
    TokenType.NUM: "número",
    TokenType.EOF: "fim do arquivo",
    **{tipo: f"'{simbolo}'" for simbolo, tipo in SYMBOLS.items()},
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int

    def __str__(self) -> str:
        return f"<{self.type.name}, '{self.lexeme}', linha {self.line}>"
