# VIERNES 2.0 — Pipeline comercial persistente
# No envía mensajes ni modifica app.py.
# Busca oportunidades, las guarda, cualifica y prepara propuestas
# para revisión humana.

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from buscador_web import buscar_web


RUTA_BD = Path("data") / "viernes_comercial.db"

ESTADOS = (
    "descubierto",
    "cualificado",
    "propuesta_pendiente_revision",
    "propuesta_enviada",
    "contactado",
    "respuesta",
    "prueba",
    "conversion",
    "descartado",
)

ESTADOS_EXTERNOS = {
    "propuesta_enviada",
    "contactado",
    "respuesta",
    "prueba",
    "conversion",
}

PALABRAS_INTENCION = (
    "looking for",
    "need",
    "seeking",
    "hiring",
    "request",
    "alternative",
    "web scraping",
    "scraping",
    "data extraction",
    "data extractor",
    "api",
    "automation",
    "automatización",
    "busco",
    "necesito",
    "buscamos",
    "contratar",
    "extraer datos",
)

PALABRAS_DESCARTE = (
    "tutorial",
    "course",
    "curso",
    "documentation",
    "documentación",
    "wikipedia",
)


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def abrir_base_datos():
    RUTA_BD.parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_o_persona TEXT NOT NULL,
            dominio TEXT,
            necesidad_detectada TEXT NOT NULL,
            url_fuente TEXT NOT NULL UNIQUE,
            titulo_fuente TEXT,
            extracto_fuente TEXT,
            nicho TEXT NOT NULL,
            consulta_origen TEXT NOT NULL,
            fecha_descubrimiento TEXT NOT NULL,
            puntuacion INTEGER NOT NULL,
            explicacion_puntuacion TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'descubierto',
            propuesta TEXT,
            ingreso_usd REAL NOT NULL DEFAULT 0,
            notas TEXT,
            fecha_ultima_actualizacion TEXT NOT NULL
        )
        """
    )

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS historial_lead (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            estado_anterior TEXT,
            estado_nuevo TEXT NOT NULL,
            nota TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
        """
    )

    conexion.commit()
    return conexion


def obtener_texto(resultado):
    return " ".join(
        [
            str(resultado.get("titulo", "")),
            str(resultado.get("contenido", "")),
            str(resultado.get("url", "")),
        ]
    ).lower()


def puntuar_lead(resultado):
    texto = obtener_texto(resultado)

    coincidencias = [
        palabra
        for palabra in PALABRAS_INTENCION
        if palabra in texto
    ]

    descartes = [
        palabra
        for palabra in PALABRAS_DESCARTE
        if palabra in texto
    ]

    puntuacion = min(len(coincidencias) * 12, 60)

    contenido = str(resultado.get("contenido", "")).strip()

    if len(contenido) >= 180:
        puntuacion += 15

    if urlparse(str(resultado.get("url", ""))).netloc:
        puntuacion += 10

    puntuacion -= min(len(descartes) * 15, 30)
    puntuacion = max(0, min(100, puntuacion))

    explicacion = []

    if coincidencias:
        explicacion.append(
            "Señales detectadas: " + ", ".join(coincidencias[:5])
        )
    else:
        explicacion.append(
            "No hay señales claras de intención de compra"
        )

    if len(contenido) >= 180:
        explicacion.append("El resultado contiene contexto suficiente")

    if descartes:
        explicacion.append(
            "Penalización: " + ", ".join(descartes[:3])
        )

    return puntuacion, ". ".join(explicacion)


def identificar_empresa(resultado):
    url = str(resultado.get("url", "")).strip()
    dominio = urlparse(url).netloc.lower().replace("www.", "")
    titulo = str(resultado.get("titulo", "")).strip()

    if dominio:
        return dominio, dominio

    if titulo:
        return titulo[:255], ""

    return "Entidad sin identificar", ""


def descubrir_leads(conexion, nicho, consulta):
    resultados = buscar_web(consulta)

    resumen = {
        "resultados_tavily": len(resultados),
        "leads_guardados": 0,
        "duplicados": 0,
        "cualificados": 0,
    }

    for resultado in resultados:
        url = str(resultado.get("url", "")).strip()

        if not url:
            continue

        empresa, dominio = identificar_empresa(resultado)
        puntuacion, explicacion = puntuar_lead(resultado)

        if puntuacion >= 45:
            estado = "cualificado"
        else:
            estado = "descubierto"

        contenido = str(resultado.get("contenido", "")).strip()
        titulo = str(resultado.get("titulo", "")).strip()
        fecha = ahora()

        try:
            cursor = conexion.execute(
                """
                INSERT INTO leads (
                    empresa_o_persona,
                    dominio,
                    necesidad_detectada,
                    url_fuente,
                    titulo_fuente,
                    extracto_fuente,
                    nicho,
                    consulta_origen,
                    fecha_descubrimiento,
                    puntuacion,
                    explicacion_puntuacion,
                    estado,
                    fecha_ultima_actualizacion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    empresa,
                    dominio,
                    contenido[:4000] or titulo,
                    url,
                    titulo[:500],
                    contenido[:4000],
                    nicho,
                    consulta,
                    fecha,
                    puntuacion,
                    explicacion,
                    estado,
                    fecha,
                ),
            )

            lead_id = cursor.lastrowid

            conexion.execute(
                """
                INSERT INTO historial_lead (
                    lead_id,
                    fecha,
                    estado_anterior,
                    estado_nuevo,
                    nota
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    fecha,
                    None,
                    estado,
                    "Lead descubierto mediante Tavily",
                ),
            )

            resumen["leads_guardados"] += 1

            if estado == "cualificado":
                resumen["cualificados"] += 1

        except sqlite3.IntegrityError:
            resumen["duplicados"] += 1

    conexion.commit()
    return resumen


def listar_leads(conexion, estado=None):
    sql = """
        SELECT
            id,
            empresa_o_persona,
            puntuacion,
            estado,
            url_fuente
        FROM leads
    """

    parametros = []

    if estado:
        sql += " WHERE estado = ?"
        parametros.append(estado)

    sql += " ORDER BY puntuacion DESC, id DESC"

    filas = conexion.execute(sql, parametros).fetchall()

    if not filas:
        print("No hay leads.")
        return

    for lead in filas:
        print(
            f"#{lead['id']} | "
            f"{lead['puntuacion']}/100 | "
            f"{lead['estado']} | "
            f"{lead['empresa_o_persona']}"
        )
        print(f"  {lead['url_fuente']}")

    print(f"\nTotal: {len(filas)}")


def generar_propuesta(conexion, lead_id):
    lead = conexion.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    if lead is None:
        raise ValueError("El lead no existe.")

    if lead["estado"] not in (
        "cualificado",
        "propuesta_pendiente_revision",
    ):
        raise ValueError(
            "Solo se pueden preparar propuestas para leads cualificados."
        )

    evidencia = (
        lead["extracto_fuente"]
        or lead["necesidad_detectada"]
        or ""
    ).replace("\n", " ").strip()[:280]

    propuesta = (
        f"Hola, vi que {lead['empresa_o_persona']} podría tener una "
        f"necesidad relacionada con datos web: «{evidencia}».\n\n"
        "VIERNES Data Extractor ofrece búsquedas y extracción "
        "estructurada mediante API para integrar datos web en "
        "procesos internos sin construir el motor desde cero.\n\n"
        "Podemos preparar una prueba limitada adaptada a vuestro "
        "caso de uso. ¿Tiene sentido revisar un ejemplo?"
    )

    fecha = ahora()

    conexion.execute(
        """
        UPDATE leads
        SET propuesta = ?,
            estado = ?,
            fecha_ultima_actualizacion = ?
        WHERE id = ?
        """,
        (
            propuesta,
            "propuesta_pendiente_revision",
            fecha,
            lead_id,
        ),
    )

    conexion.execute(
        """
        INSERT INTO historial_lead (
            lead_id,
            fecha,
            estado_anterior,
            estado_nuevo,
            nota
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            fecha,
            lead["estado"],
            "propuesta_pendiente_revision",
            "Propuesta creada. Requiere revisión humana.",
        ),
    )

    conexion.commit()

    print(propuesta)


def actualizar_estado(
    conexion,
    lead_id,
    nuevo_estado,
    nota,
    ingreso_usd,
    confirmacion_humana,
):
    if nuevo_estado not in ESTADOS:
        raise ValueError("Estado inválido.")

    if nuevo_estado in ESTADOS_EXTERNOS and not confirmacion_humana:
        raise ValueError(
            "Para registrar contacto, respuesta, prueba o conversión "
            "debes usar --confirmacion-humana después de una acción real."
        )

    lead = conexion.execute(
        "SELECT estado FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    if lead is None:
        raise ValueError("El lead no existe.")

    fecha = ahora()

    conexion.execute(
        """
        UPDATE leads
        SET estado = ?,
            notas = ?,
            ingreso_usd = ?,
            fecha_ultima_actualizacion = ?
        WHERE id = ?
        """,
        (
            nuevo_estado,
            nota,
            ingreso_usd,
            fecha,
            lead_id,
        ),
    )

    conexion.execute(
        """
        INSERT INTO historial_lead (
            lead_id,
            fecha,
            estado_anterior,
            estado_nuevo,
            nota
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            fecha,
            lead["estado"],
            nuevo_estado,
            nota,
        ),
    )

    conexion.commit()
    print("Lead actualizado.")


def mostrar_metricas(conexion):
    total = conexion.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    ingresos = conexion.execute(
        "SELECT COALESCE(SUM(ingreso_usd), 0) FROM leads"
    ).fetchone()[0]

    filas = conexion.execute(
        """
        SELECT estado, COUNT(*) AS cantidad
        FROM leads
        GROUP BY estado
        ORDER BY estado
        """
    ).fetchall()

    por_estado = {
        fila["estado"]: fila["cantidad"]
        for fila in filas
    }

    print(
        json.dumps(
            {
                "total_leads": total,
                "ingresos_usd": ingresos,
                "por_estado": por_estado,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def crear_argumentos():
    parser = argparse.ArgumentParser(
        description="Pipeline comercial de VIERNES"
    )

    subcomandos = parser.add_subparsers(
        dest="comando",
        required=True,
    )

    descubrir = subcomandos.add_parser(
        "descubrir",
        help="Busca y guarda oportunidades comerciales",
    )
    descubrir.add_argument("--nicho", required=True)
    descubrir.add_argument("--consulta", required=True)

    lista = subcomandos.add_parser(
        "lista",
        help="Lista leads guardados",
    )
    lista.add_argument(
        "--estado",
        choices=ESTADOS,
    )

    propuesta = subcomandos.add_parser(
        "propuesta",
        help="Genera una propuesta para revisión humana",
    )
    propuesta.add_argument(
        "--lead-id",
        required=True,
        type=int,
    )

    actualizar = subcomandos.add_parser(
        "actualizar",
        help="Registra una transición comercial real",
    )
    actualizar.add_argument(
        "--lead-id",
        required=True,
        type=int,
    )
    actualizar.add_argument(
        "--estado",
        required=True,
        choices=ESTADOS,
    )
    actualizar.add_argument(
        "--nota",
        default="",
    )
    actualizar.add_argument(
        "--ingreso-usd",
        default=0.0,
        type=float,
    )
    actualizar.add_argument(
        "--confirmacion-humana",
        action="store_true",
    )

    subcomandos.add_parser(
        "metricas",
        help="Muestra métricas comerciales",
    )

    return parser


def main():
    args = crear_argumentos().parse_args()
    conexion = abrir_base_datos()

    try:
        if args.comando == "descubrir":
            resumen = descubrir_leads(
                conexion,
                args.nicho,
                args.consulta,
            )
            print(json.dumps(resumen, ensure_ascii=False, indent=2))

        elif args.comando == "lista":
            listar_leads(conexion, args.estado)

        elif args.comando == "propuesta":
            generar_propuesta(conexion, args.lead_id)

        elif args.comando == "actualizar":
            actualizar_estado(
                conexion,
                args.lead_id,
                args.estado,
                args.nota,
                args.ingreso_usd,
                args.confirmacion_humana,
            )

        elif args.comando == "metricas":
            mostrar_metricas(conexion)

        return 0

    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    finally:
        conexion.close()


if __name__ == "__main__":
    raise SystemExit(main())
