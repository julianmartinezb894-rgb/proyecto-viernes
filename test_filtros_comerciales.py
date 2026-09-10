import ast
from pathlib import Path
import unittest
from urllib.parse import urlparse


# Load pure filters without importing unavailable database/search integrations.
source = Path(__file__).with_name("pipeline_comercial.py")
tree = ast.parse(source.read_text(encoding="utf-8-sig"))
names = {
    "DOMINIOS_DESCARTADOS", "EXPRESIONES_CONTENIDO_NO_COMPRADOR",
    "EXPRESIONES_DEMANDA", "EXPRESIONES_SERVICIO",
}
nodes = [
    node for node in tree.body
    if (isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in names
        for target in node.targets
    )) or (isinstance(node, ast.FunctionDef) and node.name in {
        "es_oportunidad_directa", "puntuar_lead",
    })
]
namespace = {"urlparse": urlparse}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)


class FiltrosTests(unittest.TestCase):
    def test_excluded_hosts_and_subdomains(self):
        for url in (
            "https://upwork.com/job", "https://www.upwork.com/job",
            "https://old.reddit.com/r/jobs", "https://UPWORK.COM.:443/job",
        ):
            with self.subTest(url=url):
                self.assertFalse(namespace["es_oportunidad_directa"](url))

    def test_valid_host_not_substring(self):
        for url in ("https://community.n8n.io/t/job", "https://notupwork.com/job"):
            self.assertTrue(namespace["es_oportunidad_directa"](url))

    def test_invalid_urls(self):
        for url in ("", "relative/path", "ftp://example.org/job", "https://[bad"):
            with self.subTest(url=url):
                self.assertFalse(namespace["es_oportunidad_directa"](url))

    def test_supplier_not_buyer(self):
        score, _ = namespace["puntuar_lead"]({
            "url": "https://community.n8n.io/t/provider",
            "titulo": "[For Hire] Web scraping developer",
            "contenido": "Looking for clients? Contact me for data extraction.",
        })
        self.assertEqual(score, 0)

    def test_explicit_buyer_preserved(self):
        score, _ = namespace["puntuar_lead"]({
            "url": "https://community.n8n.io/t/buyer",
            "titulo": "Looking for data extraction developer",
            "contenido": "We need web scraping. Contact us to discuss scope.",
        })
        self.assertGreater(score, 0)

    def test_paid_automation_buyer_is_compatible(self):
        score, _ = namespace["puntuar_lead"]({
            "url": "https://community.n8n.io/t/buyer",
            "titulo": "Hiring n8n automation developer",
            "contenido": "We need a paid PostgreSQL and email automation pilot.",
        })
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
