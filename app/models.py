from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


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
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil',
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
    vistas = models.PositiveIntegerField(default=0, verbose_name='Vistas')
    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Publicación',
    )
    autor = models.ForeignKey(
        'app.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Autor',
        related_name='noticias_publicadas'
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
    autor = models.ForeignKey(
        'app.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creador',
        related_name='cursos_creados'
    )

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
    es_evaluable = models.BooleanField(
        default=False,
        verbose_name='Es actividad evaluable',
        help_text='Si se marca, el usuario no podrá completarlo manualmente; dependerá de la validación del administrador.',
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


# ─────────────────────────────────────────────
# CARRUSEL PRINCIPAL
# ─────────────────────────────────────────────
class Carrusel(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título')
    subtitulo = models.TextField(verbose_name='Subtítulo')
    etiqueta = models.CharField(max_length=50, blank=True, null=True, verbose_name='Etiqueta (Ej: NUEVA PLATAFORMA)')
    imagen_fondo = models.ImageField(upload_to='carrusel/', verbose_name='Imagen de Fondo')
    
    # Enlaces
    enlace_url = models.URLField(blank=True, null=True, verbose_name='Enlace Externo (Opcional)')
    noticia_vinculada = models.ForeignKey(Noticia, on_delete=models.SET_NULL, blank=True, null=True, related_name='slides_carrusel', verbose_name='Noticia Vinculada')
    curso_vinculado = models.ForeignKey(Curso, on_delete=models.SET_NULL, blank=True, null=True, related_name='slides_carrusel', verbose_name='Curso Vinculado')
    
    texto_boton = models.CharField(max_length=50, default='Ver Detalles', verbose_name='Texto del Botón')
    
    activo = models.BooleanField(default=True, verbose_name='Activo (Mostrar en inicio)')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Diapositiva del Carrusel'
        verbose_name_plural = 'Carrusel Principal'
        ordering = ['orden', '-id']

    def __str__(self):
        return self.titulo


# ─────────────────────────────────────────────
# PROGRESO DE MÓDULO (Usuario ↔ Módulo)
# ─────────────────────────────────────────────
class ProgresoModulo(models.Model):
    """Registra que un usuario ha completado (visto) un módulo específico o el estado de su actividad evaluable."""
    
    class Estado(models.TextChoices):
        COMPLETADO = 'completado', 'Completado'
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_REVISION = 'en_revision', 'En Revisión'
        APROBADO = 'aprobado', 'Aprobado'
        CALIFICADO = 'calificado', 'Calificado'

    usuario = models.ForeignKey(
        'app.Usuario',
        on_delete=models.CASCADE,
        related_name='progreso_modulos',
        verbose_name='Usuario',
    )
    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.CASCADE,
        related_name='progresos',
        verbose_name='Módulo',
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.COMPLETADO,
        verbose_name='Estado',
    )
    calificacion = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Calificación'
    )
    retroalimentacion = models.TextField(
        blank=True, verbose_name='Retroalimentación/Observaciones'
    )
    fecha_completado = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro',
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización',
    )

    class Meta:
        verbose_name = 'Progreso de Módulo'
        verbose_name_plural = 'Progreso de Módulos'
        unique_together = ('usuario', 'modulo')
        ordering = ['fecha_completado']

    def __str__(self):
        return f'{self.usuario} completó «{self.modulo.titulo}»'


# ─────────────────────────────────────────────
# SEÑALES: Limpieza automática de archivos
# ─────────────────────────────────────────────
def _delete_file_if_exists(file_field):
    """Elimina un archivo del storage (local o S3) si existe."""
    if file_field and file_field.name:
        try:
            file_field.storage.delete(file_field.name)
            logger.info(f"Archivo eliminado del storage: {file_field.name}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar {file_field.name}: {e}")


# Modelos con campos de archivo que necesitan limpieza
_FILE_FIELD_MODELS = {
    Usuario: ['foto_perfil'],
    Noticia: ['imagen_portada'],
    Curso: ['imagen_portada'],
    Modulo: ['archivo_adjunto'],
    Carrusel: ['imagen_fondo'],
}


@receiver(pre_save)
def cleanup_old_file_on_change(sender, instance, **kwargs):
    """Antes de guardar, si cambió un archivo, elimina el anterior."""
    if sender not in _FILE_FIELD_MODELS:
        return
    if not instance.pk:
        return  # Es una creación nueva, no hay archivo viejo
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    for field_name in _FILE_FIELD_MODELS[sender]:
        old_file = getattr(old_instance, field_name)
        new_file = getattr(instance, field_name)
        if old_file and old_file.name and (not new_file or old_file.name != new_file.name):
            _delete_file_if_exists(old_file)


@receiver(post_delete)
def cleanup_files_on_delete(sender, instance, **kwargs):
    """Después de borrar un objeto, elimina sus archivos del storage."""
    if sender not in _FILE_FIELD_MODELS:
        return
    for field_name in _FILE_FIELD_MODELS[sender]:
        file_field = getattr(instance, field_name, None)
        _delete_file_if_exists(file_field)


# ─────────────────────────────────────────────
# SEÑALES: Gestión de Módulos Evaluables e Inscripciones
# ─────────────────────────────────────────────
@receiver(pre_save, sender=Inscripcion)
def handle_inscripcion_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Inscripcion.objects.get(pk=instance.pk)
            instance._was_approved = old.aprobado_por_admin
        except Inscripcion.DoesNotExist:
            instance._was_approved = False
    else:
        instance._was_approved = False

@receiver(models.signals.post_save, sender=Inscripcion)
def handle_inscripcion_post_save(sender, instance, created, **kwargs):
    if instance.aprobado_por_admin:
        # Pre-crear ProgresoModulo en estado PENDIENTE para todos los módulos evaluables del curso
        evaluable_modules = Modulo.objects.filter(curso=instance.curso, es_evaluable=True)
        for modulo in evaluable_modules:
            ProgresoModulo.objects.get_or_create(
                usuario=instance.usuario,
                modulo=modulo,
                defaults={'estado': ProgresoModulo.Estado.PENDIENTE}
            )
            
        # Enviar correo de aprobación si cambió a aprobado
        was_approved = getattr(instance, '_was_approved', False)
        if not was_approved:
            from .utils import enviar_correo_inscripcion_aprobada
            enviar_correo_inscripcion_aprobada(instance)
    
    if created and not instance.aprobado_por_admin:
        # Nueva solicitud de inscripción -> Notificar al admin
        from .utils import enviar_correo_inscripcion_pendiente
        enviar_correo_inscripcion_pendiente(instance)


@receiver(pre_save, sender=Modulo)
def handle_modulo_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Modulo.objects.get(pk=instance.pk)
            instance._old_es_evaluable = old.es_evaluable
        except Modulo.DoesNotExist:
            instance._old_es_evaluable = False
    else:
        instance._old_es_evaluable = False

@receiver(models.signals.post_save, sender=Modulo)
def handle_modulo_post_save(sender, instance, created, **kwargs):
    old_es_evaluable = getattr(instance, '_old_es_evaluable', False)
    
    if instance.es_evaluable and (created or not old_es_evaluable):
        # El módulo pasó a ser evaluable: Crear ProgresoModulo en PENDIENTE para estudiantes aprobados
        approved_enrollments = Inscripcion.objects.filter(curso=instance.curso, aprobado_por_admin=True)
        for insc in approved_enrollments:
            ProgresoModulo.objects.get_or_create(
                usuario=insc.usuario,
                modulo=instance,
                defaults={'estado': ProgresoModulo.Estado.PENDIENTE}
            )
            
    elif not instance.es_evaluable and not created and old_es_evaluable:
        # El módulo dejó de ser evaluable:
        # 1. Eliminar progresos en PENDIENTE o EN_REVISION
        ProgresoModulo.objects.filter(
            modulo=instance,
            estado__in=[ProgresoModulo.Estado.PENDIENTE, ProgresoModulo.Estado.EN_REVISION]
        ).delete()
        
        # 2. Convertir APROBADO o CALIFICADO a COMPLETADO normal
        ProgresoModulo.objects.filter(
            modulo=instance,
            estado__in=[ProgresoModulo.Estado.APROBADO, ProgresoModulo.Estado.CALIFICADO]
        ).update(
            estado=ProgresoModulo.Estado.COMPLETADO,
            calificacion=None,
            retroalimentacion=''
        )


@receiver(pre_save, sender=ProgresoModulo)
def handle_progreso_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = ProgresoModulo.objects.get(pk=instance.pk)
            instance._old_estado = old.estado
        except ProgresoModulo.DoesNotExist:
            instance._old_estado = None
    else:
        instance._old_estado = None

@receiver(models.signals.post_save, sender=ProgresoModulo)
def handle_progreso_post_save(sender, instance, created, **kwargs):
    old_estado = getattr(instance, '_old_estado', None)
    
    # Si cambió a APROBADO o CALIFICADO -> Notificar al estudiante
    if instance.estado in [ProgresoModulo.Estado.APROBADO, ProgresoModulo.Estado.CALIFICADO] and old_estado != instance.estado:
        from .utils import enviar_correo_actividad_calificada
        enviar_correo_actividad_calificada(instance)
