"""Interface de linha de comando: lê um arquivo e exibe a tradução na tela."""

import argparse
import sys

from .errors import CompilerError
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

    try:
        if args.tokens:
            print("Tokens:")
            for tok in Lexer(source).tokenize():
                print(f"  {tok}")
            print()
        translations = translate(source)
    except CompilerError as e:
        print(e, file=sys.stderr)
        return 1

    if not translations:
        print("Programa válido, mas nenhuma expressão foi encontrada.")
    for expr in translations:
        print(expr)
    return 0
