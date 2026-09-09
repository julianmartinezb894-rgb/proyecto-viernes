import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from buscador_web import buscar_web


ESTADOS_RECALIFICABLES = (
    "descubierto",
    "cualificado",
)

EXPRESIONES_DEMANDA = (
    "looking for",
    "we need",
    "i need",
    "seeking",
    "needed",
    "required",
    "build",
    "develop",
    "developer",
    "specialist",
    "freelancer",
)


def ahora():
    return datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )


def es_oferta_upwork(url):
    datos_url = urlparse(url)

    dominio = datos_url.netloc.lower().replace(
        "www.",
        ""
    )

    ruta = datos_url.path.lower()

    return (
        dominio == "upwork.com"
        and "/freelance-jobs/apply/" in ruta
    )


def obtener_texto(resultado):
    return " ".join(
        [
            str(resultado.get("titulo", "")),
            str(resultado.get("contenido", "")),
            str(resultado.get("url", "")),
        ]
    ).lower()


def puntuar_lead(resultado):
    url = str(
        resultado.get("url", "")
    ).strip()

    if not es_oferta_upwork(url):
        return (
            0,
            "Fuente descartada: no es una oferta individual de Upwork."
        )

    texto = obtener_texto(resultado)

    coincidencias = [
        expresion
        for expresion in EXPRESIONES_DEMANDA
        if expresion in texto
    ]

    if not coincidencias:
        return (
            55,
            "Oferta de Upwork sin suficiente evidencia de demanda."
        )

    puntuacion = 75

    if "posted" in texto:
        puntuacion += 10

    if (
        "fixed-price" in texto
        or "hourly" in texto
        or "$" in texto
    ):
        puntuacion += 10

    contenido = str(
        resultado.get("contenido", "")
    ).strip()

    if len(contenido) >= 180:
        puntuacion += 5

    puntuacion = min(100, puntuacion)

    explicacion = (
        "Oferta individual de Upwork con demanda: "
        + ", ".join(coincidencias[:4])
    )

    return puntuacion, explicacion


def recalificar_leads_existentes(conexion):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                titulo_fuente,
                extracto_fuente,
                url_fuente,
                estado,
                puntuacion
            FROM leads
            WHERE estado = ANY(%s)
            """,
            (list(ESTADOS_RECALIFICABLES),),
        )

        leads = cursor.fetchall()

        for lead in leads:
            resultado = {
                "titulo": lead["titulo_fuente"] or "",
                "contenido": lead["extracto_fuente"] or "",
                "url": lead["url_fuente"] or "",
            }

            puntuacion, explicacion = puntuar_lead(
                resultado
            )

            if puntuacion >= 70:
                estado_nuevo = "cualificado"
            else:
                estado_nuevo = "descubierto"

            if (
                puntuacion != lead["puntuacion"]
                or estado_nuevo != lead["estado"]
            ):
                fecha = ahora()

                cursor.execute(
                    """
                    UPDATE leads
                    SET puntuacion = %s,
                        explicacion_puntuacion = %s,
                        estado = %s,
                        fecha_ultima_actualizacion = %s
                    WHERE id = %s
                    """,
                    (
                        puntuacion,
                        explicacion,
                        estado_nuevo,
                        fecha,
                        lead["id"],
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
                        lead["id"],
                        fecha,
                        lead["estado"],
                        estado_nuevo,
                        "Recalificación: solo ofertas individuales de Upwork.",
                    ),
                )

    conexion.commit()


def abrir_base_datos():
    database_url = os.environ.get(
        "DATABASE_URL",
        ""
    ).strip()

    if not database_url:
        raise ValueError(
            "DATABASE_URL no está configurada."
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

    recalificar_leads_existentes(conexion)

    return conexion


def identificar_empresa(resultado):
    titulo = str(
        resultado.get("titulo", "")
    ).strip()

    if titulo:
        return titulo[:255], "upwork.com"

    return "Cliente de Upwork", "upwork.com"


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
            url = str(
                resultado.get("url", "")
            ).strip()

            if not url:
                continue

            empresa, dominio = identificar_empresa(
                resultado
            )

            puntuacion, explicacion = puntuar_lead(
                resultado
            )

            if puntuacion >= 70:
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
                    "Oferta encontrada mediante Tavily.",
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
                extracto_fuente,
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
        "ingresos_usd": float(
            totales["ingresos_usd"]
        ),
        "por_estado": por_estado,
    }
