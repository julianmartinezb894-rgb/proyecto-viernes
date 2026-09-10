import os
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr


def validar_destinatario(direccion):
    valor = str(direccion or "").strip()
    _, correo = parseaddr(valor)
    if not correo or correo != valor or "@" not in correo:
        raise ValueError("El destinatario de correo no es válido.")
    return correo


def limite_diario_envios():
    try:
        limite = int(os.environ.get("VIERNES_MAX_ENVIOS_DIARIOS", "0"))
    except ValueError as error:
        raise ValueError("VIERNES_MAX_ENVIOS_DIARIOS debe ser un entero.") from error
    if not 0 <= limite <= 10:
        raise ValueError("VIERNES_MAX_ENVIOS_DIARIOS debe estar entre 0 y 10.")
    return limite


def enviar_correo(destinatario, asunto, contenido):
    correo = validar_destinatario(destinatario)
    usuario = os.environ.get("VIERNES_SMTP_USERNAME", "").strip()
    clave = os.environ.get("VIERNES_SMTP_APP_PASSWORD", "").strip()
    host = os.environ.get("VIERNES_SMTP_HOST", "smtp.gmail.com").strip()
    puerto = int(os.environ.get("VIERNES_SMTP_PORT", "465"))
    if not usuario or not clave or not host:
        raise ValueError("La configuración SMTP de VIERNES está incompleta.")

    mensaje = EmailMessage()
    mensaje["From"] = usuario
    mensaje["To"] = correo
    mensaje["Subject"] = str(asunto).replace("\r", " ").replace("\n", " ")[:160]
    mensaje.set_content(str(contenido))

    with smtplib.SMTP_SSL(host, puerto, timeout=20) as servidor:
        servidor.login(usuario, clave)
        servidor.send_message(mensaje)
