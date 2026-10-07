"""Tabela de símbolos com escopos aninhados (um escopo por bloco).

Segue a ideia da seção 2.7 do livro do Aho et al.: cada bloco `{ }` abre um
novo escopo; a busca por um nome começa no escopo mais interno e sobe até o
mais externo. Assim, uma declaração em bloco interno pode "esconder" outra
de mesmo nome em bloco externo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    type: str  # "int" ou "float"
    line: int  # linha da declaração


class SymbolTable:
    def __init__(self):
        self._scopes: list[dict[str, Symbol]] = []

    def push_scope(self) -> None:
        self._scopes.append({})

    def pop_scope(self) -> None:
        self._scopes.pop()

    def declare(self, symbol: Symbol) -> Symbol | None:
        """Declara no escopo atual. Se o nome já existir *neste* escopo,
        não sobrescreve e devolve a declaração anterior."""
        scope = self._scopes[-1]
        if symbol.name in scope:
            return scope[symbol.name]
        scope[symbol.name] = symbol
        return None

    def lookup(self, name: str) -> Symbol | None:
        """Procura do escopo mais interno para o mais externo."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None
