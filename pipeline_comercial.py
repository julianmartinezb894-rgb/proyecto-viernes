import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from buscador_web import buscar_web


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
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise ValueError(
            "DATABASE_URL no está configurada en Render."
        )

    conexion = psycopg.connect(
        database_url,
        row_factory=dict_row
    )

    with conexion.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id BIGSERIAL PRIMARY KEY,
                empresa_o_persona TEXT NOT NULL,
                dominio TEXT,
                necesidad_detectada TEXT NOT NULL,
                url_fuente TEXT NOT NULL UNIQUE,
                titulo_fuente TEXT,
                extracto_fuente TEXT,
                nicho TEXT NOT NULL,
                consulta_origen TEXT NOT NULL,
                fecha_descubrimiento TIMESTAMPTZ NOT NULL,
                puntuacion INTEGER NOT NULL,
                explicacion_puntuacion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'descubierto',
                propuesta TEXT,
                ingreso_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                notas TEXT,
                fecha_ultima_actualizacion TIMESTAMPTZ NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historial_lead (
                id BIGSERIAL PRIMARY KEY,
                lead_id BIGINT NOT NULL REFERENCES leads(id),
                fecha TIMESTAMPTZ NOT NULL,
                estado_anterior TEXT,
                estado_nuevo TEXT NOT NULL,
                nota TEXT
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
            "Sin señales claras de intención de compra"
        )

    if len(contenido) >= 180:
        explicacion.append(
            "Resultado con contexto suficiente"
        )

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

    with conexion.cursor() as cursor:
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

            contenido = str(
                resultado.get("contenido", "")
            ).strip()

            titulo = str(
                resultado.get("titulo", "")
            ).strip()

            fecha = ahora()

            cursor.execute(
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
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (url_fuente) DO NOTHING
                RETURNING id
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

            fila = cursor.fetchone()

            if fila is None:
                resumen["duplicados"] += 1
                continue

            cursor.execute(
                """
                INSERT INTO historial_lead (
                    lead_id,
                    fecha,
                    estado_anterior,
                    estado_nuevo,
                    nota
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    fila["id"],
                    fecha,
                    None,
                    estado,
                    "Lead descubierto mediante Tavily",
                ),
            )

            resumen["leads_guardados"] += 1

            if estado == "cualificado":
                resumen["cualificados"] += 1

    conexion.commit()
    return resumen


def obtener_leads(conexion, limite=20):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                empresa_o_persona,
                dominio,
                necesidad_detectada,
                url_fuente,
                titulo_fuente,
                nicho,
                puntuacion,
                explicacion_puntuacion,
                estado,
                propuesta,
                ingreso_usd,
                fecha_descubrimiento
            FROM leads
            ORDER BY puntuacion DESC, id DESC
            LIMIT %s
            """,
            (limite,),
        )

        return cursor.fetchall()


def obtener_metricas(conexion):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_leads,
                COALESCE(SUM(ingreso_usd), 0) AS ingresos_usd
            FROM leads
            """
        )

        totales = cursor.fetchone()

        cursor.execute(
            """
            SELECT estado, COUNT(*) AS cantidad
            FROM leads
            GROUP BY estado
            ORDER BY estado
            """
        )

        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in cursor.fetchall()
        }

    return {
        "total_leads": totales["total_leads"],
        "ingresos_usd": float(totales["ingresos_usd"]),
        "por_estado": por_estado,
    }


def generar_propuesta(conexion, lead_id):
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM leads WHERE id = %s",
            (lead_id,),
        )

        lead = cursor.fetchone()

        if lead is None:
            raise ValueError("El lead no existe.")

        if lead["estado"] not in (
            "cualificado",
            "propuesta_pendiente_revision",
        ):
            raise ValueError(
                "El lead debe estar cualificado."
            )

        evidencia = (
            lead["extracto_fuente"]
            or lead["necesidad_detectada"]
            or ""
        ).replace("\n", " ").strip()[:280]

        propuesta = (
            f"Hola, vi que {lead['empresa_o_persona']} podría "
            f"tener una necesidad relacionada con datos web: "
            f"«{evidencia}».\n\n"
            "VIERNES Data Extractor ofrece búsquedas y extracción "
            "estructurada mediante API para integrar datos web en "
            "procesos internos sin construir el motor desde cero.\n\n"
            "Podemos preparar una prueba limitada adaptada a vuestro "
            "caso de uso. ¿Tiene sentido revisar un ejemplo?"
        )

        fecha = ahora()

        cursor.execute(
            """
            UPDATE leads
            SET propuesta = %s,
                estado = %s,
                fecha_ultima_actualizacion = %s
            WHERE id = %s
            """,
            (
                propuesta,
                "propuesta_pendiente_revision",
                fecha,
                lead_id,
            ),
        )

        cursor.execute(
            """
            INSERT INTO historial_lead (
                lead_id,
                fecha,
                estado_anterior,
                estado_nuevo,
                nota
            )
            VALUES (%s, %s, %s, %s, %s)
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
    return propuesta


if __name__ == "__main__":
    try:
        conexion = abrir_base_datos()
        print(
            json.dumps(
                obtener_metricas(conexion),
                ensure_ascii=False,
                indent=2,
            )
        )
        conexion.close()

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
