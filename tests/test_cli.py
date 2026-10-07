import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from matexpr.cli import main

EXEMPLOS = os.path.join(os.path.dirname(__file__), "..", "exemplos")


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class TestCLI(unittest.TestCase):
    def test_exemplo_valido(self):
        code, out, err = run(os.path.join(EXEMPLOS, "valido.txt"))
        self.assertEqual(code, 0, err)
        self.assertEqual(
            out.splitlines(),
            ["a b c * +", "a b + c *", "a b - c -", "10 2.5 / x *", "d a 3.14 - * 2 /"],
        )

    def test_exemplos_com_erro(self):
        casos = {
            "erro_ponto_virgula.txt": "Erro sintático na linha 3",
            "erro_lexico.txt": "Erro léxico na linha 3",
            "erro_identificador.txt": "Erro léxico na linha 2",
            "erro_chave.txt": "Erro sintático na linha 4",
        }
        for arquivo, esperado in casos.items():
            with self.subTest(arquivo=arquivo):
                code, out, err = run(os.path.join(EXEMPLOS, arquivo))
                self.assertEqual(code, 1)
                self.assertIn(esperado, err)

    def test_arquivo_inexistente(self):
        code, _, err = run("nao_existe.txt")
        self.assertEqual(code, 2)
        self.assertIn("Erro ao abrir", err)

    def test_opcao_tokens(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Matexpr { a; }")
        try:
            code, out, _ = run("--tokens", f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(code, 0)
        self.assertIn("<MATEXPR, 'Matexpr', linha 1>", out)
        self.assertTrue(out.rstrip().endswith("a"))


if __name__ == "__main__":
    unittest.main()
