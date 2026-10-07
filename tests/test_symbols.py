import unittest

from matexpr.errors import SemanticWarning
from matexpr.parser import translate
from matexpr.symbols import Symbol, SymbolTable


class TestSymbolTable(unittest.TestCase):
    def setUp(self):
        self.st = SymbolTable()
        self.st.push_scope()

    def test_declara_e_busca(self):
        self.assertIsNone(self.st.declare(Symbol("a", "int", 1)))
        self.assertEqual(self.st.lookup("a"), Symbol("a", "int", 1))
        self.assertIsNone(self.st.lookup("b"))

    def test_redeclaracao_no_mesmo_escopo_devolve_anterior(self):
        self.st.declare(Symbol("a", "int", 1))
        self.assertEqual(self.st.declare(Symbol("a", "float", 2)), Symbol("a", "int", 1))
        self.assertEqual(self.st.lookup("a").type, "int")

    def test_escopo_interno_ve_externo(self):
        self.st.declare(Symbol("a", "int", 1))
        self.st.push_scope()
        self.assertEqual(self.st.lookup("a").line, 1)

    def test_escopo_interno_esconde_externo(self):
        self.st.declare(Symbol("a", "int", 1))
        self.st.push_scope()
        self.assertIsNone(self.st.declare(Symbol("a", "float", 5)))
        self.assertEqual(self.st.lookup("a").type, "float")
        self.st.pop_scope()
        self.assertEqual(self.st.lookup("a").type, "int")

    def test_declaracao_some_ao_sair_do_escopo(self):
        self.st.push_scope()
        self.st.declare(Symbol("b", "int", 3))
        self.st.pop_scope()
        self.assertIsNone(self.st.lookup("b"))


def warnings(src):
    result = translate(src)
    assert result.ok, [str(e) for e in result.errors]
    return result.warnings


class TestAvisosSemanticos(unittest.TestCase):
    def test_sem_avisos_quando_tudo_declarado(self):
        self.assertEqual(warnings("Matexpr { int a; float b; a + b; }"), [])

    def test_variavel_nao_declarada(self):
        ws = warnings("Matexpr {\n int a;\n a + b;\n}")
        self.assertEqual(len(ws), 1)
        self.assertIsInstance(ws[0], SemanticWarning)
        self.assertEqual(str(ws[0]), "Aviso na linha 3: variável 'b' não declarada")

    def test_aviso_nao_impede_traducao(self):
        result = translate("Matexpr { x * 2; }")
        self.assertTrue(result.ok)
        self.assertEqual(result.translations, ["x 2 *"])
        self.assertEqual(len(result.warnings), 1)

    def test_avisa_uma_vez_por_nome(self):
        ws = warnings("Matexpr {\n x;\n x + x;\n y;\n}")
        self.assertEqual([(w.line, "'x'" in str(w)) for w in ws], [(2, True), (4, False)])

    def test_redeclaracao_no_mesmo_bloco(self):
        ws = warnings("Matexpr {\n int a;\n float a;\n a;\n}")
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws[0].line, 3)
        self.assertIn("já declarada neste bloco na linha 2", str(ws[0]))

    def test_bloco_interno_ve_declaracao_externa(self):
        self.assertEqual(warnings("Matexpr { int a; { a + 1; { a; } } }"), [])

    def test_bloco_interno_pode_redeclarar(self):
        self.assertEqual(warnings("Matexpr { int a; { float a; a; } a; }"), [])

    def test_declaracao_interna_nao_vale_fora_do_bloco(self):
        ws = warnings("Matexpr {\n { int b; b; }\n b;\n}")
        self.assertEqual([w.line for w in ws], [3])

    def test_avisos_tambem_retornados_quando_ha_erros(self):
        result = translate("Matexpr { int a; x; a + ; }")
        self.assertFalse(result.ok)
        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()
