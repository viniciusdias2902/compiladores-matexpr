"""Interface de linha de comando: lê um arquivo e exibe a tradução na tela."""

import argparse
import sys

from .lexer import Lexer
from .parser import translate


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="matexpr",
        description="Traduz expressões aritméticas infixas para notação pós-fixada.",
    )
    ap.add_argument("arquivo", help="arquivo de entrada com o programa Matexpr")
    ap.add_argument("--tokens", action="store_true", help="exibe também os tokens reconhecidos")
    args = ap.parse_args(argv)

    try:
        with open(args.arquivo, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Erro ao abrir '{args.arquivo}': {e.strerror}", file=sys.stderr)
        return 2

    if args.tokens:
        print("Tokens:")
        for tok in Lexer(source).tokenize():
            print(f"  {tok}")
        print()

    result = translate(source)
    for diag in sorted(result.errors + result.warnings, key=lambda d: d.line):
        print(diag, file=sys.stderr)
    if not result.ok:
        print(f"{len(result.errors)} erro(s) encontrado(s).", file=sys.stderr)
        return 1

    if not result.translations:
        print("Programa válido, mas nenhuma expressão foi encontrada.")
    for expr in result.translations:
        print(expr)
    return 0
