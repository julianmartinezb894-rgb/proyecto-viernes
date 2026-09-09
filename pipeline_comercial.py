import json
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
    "hiring",
    "needed",
    "required",
)

EXPRESIONES_SERVICIO = (
    "web scraping",
    "data extraction",
    "data scraping",
    "web crawler",
    "data collection",
    "scrape data",
)

DOMINIOS_DESCARTADOS = (
    "upwork.com",
    "reddit.com",
    "medium.com",
    "youtube.com",
    "github.com",
    "browserless.io",
    "xbyte.io",
    "visualping.io",
    "ficstar.medium.com",
    "skyvia.com",
    "acceldata.io",
    "scrapethissite.com",
    "webscraper.io",
    "scrapingbee.com",
    "uniquesdata.com",
    "blog.datahut.co",
    "browse.ai",
)

EXPRESIONES_CONTENIDO_NO_COMPRADOR = (
    "best web scraping",
    "top web scraping",
    "web scraping tools",
    "web scraper tools",
    "how to web scrape",
    "how to scrape",
    "guide to web scraping",
    "learn web scraping",
    "web scraping tutorial",
    "web scraping api",
    "api access",
    "companies offering",
    "data extraction tools",
)

ESTRATEGIAS_AUTONOMAS = {
    "oferta_directa": {
        "canal": "prospeccion_directa",
        "nicho": "oportunidades directas de extracción de datos",
        "consultas": (
            '"looking for" "web scraping" -site:upwork.com -site:reddit.com',
            '"need" "data extraction" -site:upwork.com -site:reddit.com',
            '"seeking" "web scraping" -site:upwork.com -site:reddit.com',
        ),
    },
    "rfp_publica": {
        "canal": "solicitudes_publicas",
        "nicho": "solicitudes públicas de extracción de datos",
        "consultas": (
            '"request for proposal" "web scraping"',
            '"request for quotation" "data extraction"',
            '"RFP" "data collection API"',
        ),
    },
}

MAX_FALLOS_CONSECUTIVOS = 3


def ahora():
    return datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )


def es_oportunidad_directa(url):
    datos_url = urlparse(url)
    dominio = datos_url.netloc.lower().replace(
        "www.",
        ""
    )
    return bool(dominio) and dominio not in DOMINIOS_DESCARTADOS


def puntuar_lead(resultado):
    url = str(
        resultado.get("url", "")
    ).strip()

    if not es_oportunidad_directa(url):
        return (
            0,
            "Fuente descartada: no es una oportunidad comercial directa."
        )

    titulo = str(resultado.get("titulo", "")).lower()
    evidencia_inicial = " ".join(
        [
            titulo,
            str(resultado.get("contenido", ""))[:700].lower(),
        ]
    )

    descartes = [
        expresion
        for expresion in EXPRESIONES_CONTENIDO_NO_COMPRADOR
        if expresion in titulo
    ]

    if descartes:
        return (
            0,
            "Fuente descartada: contenido o proveedor, no comprador: "
            + ", ".join(descartes[:2]),
        )

    coincidencias = [
        expresion
        for expresion in EXPRESIONES_DEMANDA
        if expresion in evidencia_inicial
    ]

    servicios = [
        expresion
        for expresion in EXPRESIONES_SERVICIO
        if expresion in evidencia_inicial
    ]

    if not coincidencias or not servicios:
        return (
            0,
            "Sin evidencia temprana de demanda comercial y servicio compatible."
        )

    puntuacion = 55

    tiene_contacto = (
        "contact" in evidencia_inicial
        or "email" in evidencia_inicial
    )

    tiene_intencion_de_cotizar = (
        "request a quote" in evidencia_inicial
        or "get a quote" in evidencia_inicial
        or "pricing" in evidencia_inicial
    )

    if tiene_contacto:
        puntuacion += 10

    if tiene_intencion_de_cotizar:
        puntuacion += 10

    contenido = str(
        resultado.get("contenido", "")
    ).strip()

    if len(contenido) >= 180:
        puntuacion += 5

    if not tiene_contacto and not tiene_intencion_de_cotizar:
        puntuacion = min(puntuacion, 60)

    puntuacion = min(100, puntuacion)

    explicacion = (
        "Oportunidad directa con demanda: "
        + ", ".join(coincidencias[:3])
        + "; servicio compatible: "
        + ", ".join(servicios[:2])
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
            elif puntuacion == 0:
                estado_nuevo = "descartado"
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

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS objetivos_comerciales (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL UNIQUE,
                servicio TEXT NOT NULL,
                meta_ingresos_usd NUMERIC(12, 2) NOT NULL,
                presupuesto_maximo_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                ingresos_confirmados_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                estado TEXT NOT NULL DEFAULT 'activo',
                fecha_creacion TIMESTAMPTZ NOT NULL,
                fecha_ultima_actualizacion TIMESTAMPTZ NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS estrategias_comerciales (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL UNIQUE,
                canal TEXT NOT NULL,
                intentos INTEGER NOT NULL DEFAULT 0,
                aprobaciones INTEGER NOT NULL DEFAULT 0,
                rechazos INTEGER NOT NULL DEFAULT 0,
                respuestas INTEGER NOT NULL DEFAULT 0,
                conversiones INTEGER NOT NULL DEFAULT 0,
                ingresos_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                coste_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                puntuacion_estrategia NUMERIC(8, 2) NOT NULL DEFAULT 50,
                estado TEXT NOT NULL DEFAULT 'activa',
                fecha_ultima_actualizacion TIMESTAMPTZ NOT NULL
            )
            """
        )

        cursor.execute(
            """
            ALTER TABLE estrategias_comerciales
            ADD COLUMN IF NOT EXISTS fallos_consecutivos INTEGER NOT NULL DEFAULT 0
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ciclos_agente (
                id BIGSERIAL PRIMARY KEY,
                objetivo_id BIGINT NOT NULL REFERENCES objetivos_comerciales(id),
                estrategia_id BIGINT NOT NULL REFERENCES estrategias_comerciales(id),
                estado TEXT NOT NULL,
                resultados_encontrados INTEGER NOT NULL DEFAULT 0,
                leads_guardados INTEGER NOT NULL DEFAULT 0,
                leads_cualificados INTEGER NOT NULL DEFAULT 0,
                mensaje TEXT NOT NULL,
                fecha TIMESTAMPTZ NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS acciones_comerciales (
                id BIGSERIAL PRIMARY KEY,
                objetivo_id BIGINT NOT NULL REFERENCES objetivos_comerciales(id),
                estrategia_id BIGINT NOT NULL REFERENCES estrategias_comerciales(id),
                lead_id BIGINT NOT NULL REFERENCES leads(id),
                tipo_accion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente_aprobacion',
                prioridad NUMERIC(8, 2) NOT NULL,
                razon_decision TEXT NOT NULL,
                contenido TEXT NOT NULL,
                valor_estimado_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                coste_estimado_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                resultado JSONB,
                nota_humana TEXT,
                fecha_creacion TIMESTAMPTZ NOT NULL,
                fecha_decision TIMESTAMPTZ,
                fecha_ejecucion TIMESTAMPTZ
            )
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                una_accion_abierta_por_lead
            ON acciones_comerciales (lead_id)
            WHERE estado IN (
                'pendiente_aprobacion',
                'aprobada_pendiente_ejecucion'
            )
            """
        )

        cursor.execute(
            """
            UPDATE leads
            SET puntuacion = 0,
                explicacion_puntuacion = %s,
                fecha_ultima_actualizacion = %s
            WHERE estado = 'descartado'
              AND dominio = ANY(%s)
              AND puntuacion <> 0
            """,
            (
                "Fuente descartada por política comercial vigente.",
                ahora(),
                list(DOMINIOS_DESCARTADOS),
            ),
        )

    conexion.commit()

    recalificar_leads_existentes(conexion)

    return conexion


def identificar_empresa(resultado):
    titulo = str(
        resultado.get("titulo", "")
    ).strip()

    dominio = urlparse(
        str(resultado.get("url", ""))
    ).netloc.lower().replace("www.", "")

    if titulo:
        return titulo[:255], dominio[:255]

    return dominio or "Entidad sin identificar", dominio[:255]


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
            elif puntuacion == 0:
                estado = "descartado"
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


def asegurar_objetivo_y_estrategia(conexion):
    fecha = ahora()
    meta = float(os.environ.get("VIERNES_META_INGRESOS_USD", "100"))
    presupuesto = float(os.environ.get("VIERNES_PRESUPUESTO_MAXIMO_USD", "0"))

    with conexion.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO objetivos_comerciales (
                nombre, servicio, meta_ingresos_usd,
                presupuesto_maximo_usd, fecha_creacion,
                fecha_ultima_actualizacion
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (nombre) DO UPDATE
            SET meta_ingresos_usd = EXCLUDED.meta_ingresos_usd,
                presupuesto_maximo_usd = EXCLUDED.presupuesto_maximo_usd,
                fecha_ultima_actualizacion = EXCLUDED.fecha_ultima_actualizacion
            RETURNING *
            """,
            (
                "primer_ingreso",
                "Extracción de datos entregada como JSON, CSV o API",
                meta,
                presupuesto,
                fecha,
                fecha,
            ),
        )
        objetivo = cursor.fetchone()

        for nombre, configuracion in ESTRATEGIAS_AUTONOMAS.items():
            cursor.execute(
                """
                INSERT INTO estrategias_comerciales (
                    nombre, canal, fecha_ultima_actualizacion
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (nombre) DO UPDATE
                SET canal = EXCLUDED.canal,
                    fecha_ultima_actualizacion = EXCLUDED.fecha_ultima_actualizacion
                """,
                (nombre, configuracion["canal"], fecha),
            )

        cursor.execute(
            """
            SELECT *
            FROM estrategias_comerciales
            WHERE nombre = ANY(%s)
              AND estado = 'activa'
              AND fallos_consecutivos < %s
            ORDER BY puntuacion_estrategia DESC,
                     fallos_consecutivos ASC,
                     id ASC
            LIMIT 1
            """,
            (list(ESTRATEGIAS_AUTONOMAS), MAX_FALLOS_CONSECUTIVOS),
        )
        estrategia = cursor.fetchone()

    conexion.commit()
    return objetivo, estrategia


def crear_oferta_comercial(lead):
    necesidad = " ".join(
        str(lead["necesidad_detectada"] or "").split()
    )[:420]
    titulo = str(lead["titulo_fuente"] or lead["empresa_o_persona"])

    return (
        f"Hello, I reviewed your request: {titulo}.\n\n"
        f"The core need I identified is: {necesidad}\n\n"
        "I can begin with a small paid pilot: one target source, the exact "
        "fields you require, and delivery as structured JSON or CSV. After "
        "we verify accuracy together, the same workflow can be expanded into "
        "a recurring process or API.\n\n"
        "Before starting, please confirm the target website, required fields, "
        "expected volume, and update frequency. I will then define the scope, "
        "delivery time, and fixed pilot price without promising untested results."
    )


def calcular_prioridad(lead, estrategia):
    prioridad = float(lead["puntuacion"])
    texto = " ".join(
        [
            str(lead["titulo_fuente"] or ""),
            str(lead["extracto_fuente"] or ""),
        ]
    ).lower()

    if "50+" in texto:
        prioridad -= 35
    elif "20 to 50" in texto or "20-50" in texto:
        prioridad -= 20

    if "hires: 1" in texto or "1 hire" in texto:
        prioridad -= 25

    if "payment verified" in texto:
        prioridad += 8

    prioridad += (float(estrategia["puntuacion_estrategia"]) - 50) * 0.2
    return max(0, min(100, round(prioridad, 2)))


def obtener_candidatos_para_accion(conexion):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT l.*
            FROM leads l
            WHERE l.estado = 'cualificado'
              AND l.dominio <> 'upwork.com'
              AND NOT EXISTS (
                  SELECT 1
                  FROM acciones_comerciales a
                  WHERE a.lead_id = l.id
              )
            ORDER BY l.puntuacion DESC, l.fecha_descubrimiento DESC
            LIMIT 25
            """
        )
        return cursor.fetchall()


def buscar_con_estrategia(conexion, estrategia):
    configuracion = ESTRATEGIAS_AUTONOMAS[estrategia["nombre"]]
    total = {
        "resultados_tavily": 0,
        "leads_guardados": 0,
        "duplicados": 0,
        "cualificados": 0,
    }

    for consulta in configuracion["consultas"]:
        resumen = descubrir_leads(
            conexion,
            configuracion["nicho"],
            consulta,
        )
        for clave in total:
            total[clave] += resumen[clave]

    return total


def registrar_ciclo(
    conexion,
    objetivo_id,
    estrategia_id,
    estado,
    resumen,
    mensaje,
):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ciclos_agente (
                objetivo_id, estrategia_id, estado,
                resultados_encontrados, leads_guardados,
                leads_cualificados, mensaje, fecha
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                objetivo_id,
                estrategia_id,
                estado,
                resumen.get("resultados_tavily", 0),
                resumen.get("leads_guardados", 0),
                resumen.get("cualificados", 0),
                mensaje,
                ahora(),
            ),
        )


def registrar_fallo_de_estrategia(conexion, estrategia):
    fecha = ahora()
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            UPDATE estrategias_comerciales
            SET intentos = intentos + 1,
                fallos_consecutivos = fallos_consecutivos + 1,
                puntuacion_estrategia = GREATEST(
                    0,
                    puntuacion_estrategia - 5
                ),
                estado = CASE
                    WHEN fallos_consecutivos + 1 >= %s THEN 'agotada'
                    ELSE estado
                END,
                fecha_ultima_actualizacion = %s
            WHERE id = %s
            RETURNING *
            """,
            (MAX_FALLOS_CONSECUTIVOS, fecha, estrategia["id"]),
        )
        return cursor.fetchone()


def ejecutar_ciclo_comercial(conexion):
    objetivo, estrategia = asegurar_objetivo_y_estrategia(conexion)

    if float(objetivo["ingresos_confirmados_usd"]) >= float(objetivo["meta_ingresos_usd"]):
        return {
            "estado": "meta_cumplida",
            "objetivo": objetivo,
            "mensaje": "La meta económica activa ya fue alcanzada.",
        }

    if estrategia is None:
        return {
            "estado": "estrategias_agotadas",
            "objetivo": objetivo,
            "mensaje": (
                "Las estrategias disponibles alcanzaron su límite de fallos. "
                "VIERNES no repetirá búsquedas improductivas."
            ),
        }

    candidatos = obtener_candidatos_para_accion(conexion)
    resumen_busqueda = {
        "resultados_tavily": 0,
        "leads_guardados": 0,
        "duplicados": 0,
        "cualificados": 0,
    }

    if not candidatos:
        resumen_busqueda = buscar_con_estrategia(conexion, estrategia)
        candidatos = obtener_candidatos_para_accion(conexion)

    if not candidatos:
        estrategia_actualizada = registrar_fallo_de_estrategia(
            conexion,
            estrategia,
        )
        mensaje = (
            "VIERNES buscó automáticamente, no encontró una oportunidad "
            "cualificada y registró el fallo para no repetir indefinidamente."
        )
        registrar_ciclo(
            conexion,
            objetivo["id"],
            estrategia["id"],
            "busqueda_sin_oportunidad",
            resumen_busqueda,
            mensaje,
        )
        conexion.commit()
        return {
            "estado": "busqueda_sin_oportunidad",
            "objetivo": objetivo,
            "estrategia": estrategia_actualizada,
            "busqueda": resumen_busqueda,
            "mensaje": mensaje,
        }

    with conexion.cursor() as cursor:

        evaluados = [
            (calcular_prioridad(lead, estrategia), lead)
            for lead in candidatos
        ]
        prioridad, lead = max(evaluados, key=lambda elemento: elemento[0])

        if prioridad < 65:
            return {
                "estado": "sin_oportunidad_rentable",
                "objetivo": objetivo,
                "mejor_prioridad": prioridad,
                "mensaje": "Las oportunidades actuales no justifican una acción.",
            }

        contenido = crear_oferta_comercial(lead)
        valor_estimado = 60.0 if prioridad < 85 else 100.0
        coste_estimado = 0.0
        fecha = ahora()
        razon = (
            f"Lead {lead['id']} seleccionado con prioridad {prioridad}/100; "
            "coincide con extracción de datos y todavía no tiene una acción registrada."
        )

        cursor.execute(
            """
            INSERT INTO acciones_comerciales (
                objetivo_id, estrategia_id, lead_id, tipo_accion,
                prioridad, razon_decision, contenido,
                valor_estimado_usd, coste_estimado_usd, fecha_creacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                objetivo["id"],
                estrategia["id"],
                lead["id"],
                "presentar_oferta",
                prioridad,
                razon,
                contenido,
                valor_estimado,
                coste_estimado,
                fecha,
            ),
        )
        accion = cursor.fetchone()

        cursor.execute(
            """
            UPDATE leads
            SET estado = 'propuesta_pendiente_revision',
                propuesta = %s,
                fecha_ultima_actualizacion = %s
            WHERE id = %s
            """,
            (contenido, fecha, lead["id"]),
        )
        cursor.execute(
            """
            INSERT INTO historial_lead (
                lead_id, fecha, estado_anterior, estado_nuevo, nota
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                lead["id"],
                fecha,
                "cualificado",
                "propuesta_pendiente_revision",
                razon,
            ),
        )
        cursor.execute(
            """
            UPDATE estrategias_comerciales
            SET intentos = intentos + 1,
                fallos_consecutivos = 0,
                fecha_ultima_actualizacion = %s
            WHERE id = %s
            """,
            (fecha, estrategia["id"]),
        )

    conexion.commit()
    registrar_ciclo(
        conexion,
        objetivo["id"],
        estrategia["id"],
        "accion_pendiente_aprobacion",
        resumen_busqueda,
        razon,
    )
    conexion.commit()
    return {
        "estado": "accion_pendiente_aprobacion",
        "objetivo": objetivo,
        "estrategia": estrategia,
        "busqueda": resumen_busqueda,
        "accion": accion,
        "intervencion_humana": "Aprobar o rechazar. VIERNES no enviará nada todavía.",
    }


def obtener_acciones_pendientes(conexion, limite=20):
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.*,
                l.empresa_o_persona,
                l.url_fuente,
                l.necesidad_detectada
            FROM acciones_comerciales a
            JOIN leads l ON l.id = a.lead_id
            WHERE a.estado IN (
                'pendiente_aprobacion',
                'aprobada_pendiente_ejecucion'
            )
            ORDER BY a.prioridad DESC, a.fecha_creacion ASC
            LIMIT %s
            """,
            (limite,),
        )
        return cursor.fetchall()


def decidir_accion(conexion, accion_id, decision, nota=""):
    if decision not in {"aprobar", "rechazar"}:
        raise ValueError("La decisión debe ser aprobar o rechazar.")

    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM acciones_comerciales
            WHERE id = %s AND estado = 'pendiente_aprobacion'
            FOR UPDATE
            """,
            (accion_id,),
        )
        accion = cursor.fetchone()
        if accion is None:
            raise ValueError("La acción no existe o ya fue decidida.")

        fecha = ahora()
        estado = (
            "aprobada_pendiente_ejecucion"
            if decision == "aprobar"
            else "rechazada"
        )
        cursor.execute(
            """
            UPDATE acciones_comerciales
            SET estado = %s, nota_humana = %s, fecha_decision = %s
            WHERE id = %s
            RETURNING *
            """,
            (estado, nota, fecha, accion_id),
        )
        actualizada = cursor.fetchone()
        cursor.execute(
            """
            UPDATE estrategias_comerciales
            SET aprobaciones = aprobaciones + %s,
                rechazos = rechazos + %s,
                puntuacion_estrategia = CASE
                    WHEN %s THEN GREATEST(0, puntuacion_estrategia - 10)
                    ELSE LEAST(100, puntuacion_estrategia + 2)
                END,
                estado = CASE
                    WHEN %s AND canal = 'oportunidad_detectada' THEN 'pausada'
                    ELSE estado
                END,
                fecha_ultima_actualizacion = %s
            WHERE id = %s
            """,
            (
                1 if decision == "aprobar" else 0,
                1 if decision == "rechazar" else 0,
                decision == "rechazar",
                decision == "rechazar",
                fecha,
                accion["estrategia_id"],
            ),
        )
        if decision == "rechazar":
            cursor.execute(
                """
                UPDATE leads
                SET estado = 'descartado',
                    puntuacion = 0,
                    explicacion_puntuacion = %s,
                    fecha_ultima_actualizacion = %s
                WHERE id = %s
                """,
                (
                    "Acción rechazada por decisión humana: " + nota,
                    fecha,
                    accion["lead_id"],
                ),
            )

    conexion.commit()
    return actualizada


def obtener_estado_agente(conexion):
    objetivo, estrategia = asegurar_objetivo_y_estrategia(conexion)
    pendientes = obtener_acciones_pendientes(conexion, limite=5)
    return {
        "objetivo_activo": objetivo,
        "estrategia_activa": estrategia,
        "acciones_pendientes": pendientes,
        "regla_humana": (
            "Solo requiere aprobación para contacto, contratos, gastos y cobros."
        ),
    }
