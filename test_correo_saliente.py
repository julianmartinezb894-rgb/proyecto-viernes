import os
import unittest
from unittest.mock import patch

import correo_saliente


class CorreoSalienteTests(unittest.TestCase):
    def test_rechaza_destinatarios_invalidos(self):
        for valor in ("", "nombre", "a@b\nBcc:x@y.com"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    correo_saliente.validar_destinatario(valor)

    def test_acepta_destinatario_simple(self):
        self.assertEqual(
            correo_saliente.validar_destinatario("buyer@example.com"),
            "buyer@example.com",
        )

    @patch.dict(os.environ, {"VIERNES_MAX_ENVIOS_DIARIOS": "0"}, clear=False)
    def test_limite_cero_desactiva_envios(self):
        self.assertEqual(correo_saliente.limite_diario_envios(), 0)

    @patch.dict(os.environ, {"VIERNES_MAX_ENVIOS_DIARIOS": "11"}, clear=False)
    def test_limite_superior_es_rechazado(self):
        with self.assertRaises(ValueError):
            correo_saliente.limite_diario_envios()


if __name__ == "__main__":
    unittest.main()
