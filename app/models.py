from django.db import models
from django.contrib.auth.models import AbstractUser


# ─────────────────────────────────────────────
# USUARIO PERSONALIZADO (con roles)
# ─────────────────────────────────────────────
class Usuario(AbstractUser):
    """
    Extiende el modelo base de Django.
    Mantiene email, password, first_name, last_name del padre.
    Agrega el campo 'rol' para diferenciar usuarios.
    """
    class Rol(models.TextChoices):
        ESTANDAR = 'estandar', 'Usuario Estándar'
        ADMINISTRADOR = 'administrador', 'Administrador'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ESTANDAR,
        verbose_name='Rol',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR


# ─────────────────────────────────────────────
# NOTICIA
# ─────────────────────────────────────────────
class Noticia(models.Model):
    titulo = models.CharField(max_length=255, verbose_name='Título')
    imagen_portada = models.ImageField(
        upload_to='noticias/',
        blank=True,
        null=True,
        verbose_name='Imagen de Portada',
    )
    contenido = models.TextField(verbose_name='Contenido')
    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Publicación',
    )

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return self.titulo


# ─────────────────────────────────────────────
# CURSO
# ─────────────────────────────────────────────
class Curso(models.Model):
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    imagen_portada = models.ImageField(
        upload_to='cursos/',
        blank=True,
        null=True,
        verbose_name='Imagen de Portada',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo


# ─────────────────────────────────────────────
# MÓDULO (pertenece a un Curso)
# ─────────────────────────────────────────────
class Modulo(models.Model):
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='modulos',
        verbose_name='Curso',
    )
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    archivo_adjunto = models.FileField(
        upload_to='modulos/archivos/',
        blank=True,
        null=True,
        verbose_name='Archivo Adjunto (PDF/Word/PPT)',
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Video (YouTube)',
        help_text='Pega aquí el enlace del video de YouTube para embeber.',
    )
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['orden']

    def __str__(self):
        return f'{self.curso.titulo} — {self.titulo}'

    @property
    def youtube_id(self):
        if not self.video_url:
            return None
        import re
        match = re.search(r'(?:v=|youtu\.be\/)([a-zA-Z0-9_-]{11})', self.video_url)
        return match.group(1) if match else None


# ─────────────────────────────────────────────
# INSCRIPCIÓN (Usuario ↔ Curso)
# ─────────────────────────────────────────────
class Inscripcion(models.Model):
    usuario = models.ForeignKey(
        'app.Usuario',
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Usuario',
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Curso',
    )
    aprobado_por_admin = models.BooleanField(
        default=False,
        verbose_name='Aprobado por Admin',
    )
    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Inscripción',
    )

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        unique_together = ('usuario', 'curso')  # Un usuario solo puede inscribirse una vez por curso
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        estado = '✔ Aprobada' if self.aprobado_por_admin else '⏳ Pendiente'
        return f'{self.usuario} → {self.curso} [{estado}]'
