import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from app.models import Carrusel
import urllib.request
from django.core.files.base import ContentFile

slides = [
    {
        "titulo": "El Hub de Innovación Estudiantil", 
        "subtitulo": "Conecta con mentes brillantes y desarrolla habilidades para el futuro.", 
        "etiqueta": "NUEVA PLATAFORMA", 
        "enlace_url": "/cursos/",
        "texto_boton": "Explorar Cursos",
        "orden": 0
    },
    {
        "titulo": "Aprende de Expertos locales", 
        "subtitulo": "Accede a cursos técnicos y talleres organizados por clubes especializados.", 
        "etiqueta": "FORMACIÓN CONTINUA", 
        "enlace_url": "/noticias/",
        "texto_boton": "Últimas Noticias",
        "orden": 1
    },
    {
        "titulo": "Lidera el Cambio", 
        "subtitulo": "Únete a un club, propón iniciativas y deja tu huella en la comunidad.", 
        "etiqueta": "LIDERAZGO", 
        "enlace_url": "#",
        "texto_boton": "Únete",
        "orden": 2
    }
]

if Carrusel.objects.count() == 0:
    for slide in slides:
        Carrusel.objects.create(
            titulo=slide['titulo'],
            subtitulo=slide['subtitulo'],
            etiqueta=slide['etiqueta'],
            enlace_url=slide['enlace_url'],
            texto_boton=slide['texto_boton'],
            orden=slide['orden'],
            activo=True
        )
    print("¡Slides por defecto creados en la Base de Datos!")
else:
    print("Ya existen slides en la base de datos.")
