from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def enviar_correo_inscripcion_pendiente(inscripcion):
    """Notifica a los admins de una nueva solicitud de inscripción."""
    from .models import Usuario
    admins = Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR).exclude(email='')
    destinatarios = [admin.email for admin in admins]
    if not destinatarios:
        destinatarios = [settings.DEFAULT_FROM_EMAIL]
        
    subject = f"Nueva solicitud de inscripción: {inscripcion.curso.titulo}"
    message = (
        f"Hola,\n\n"
        f"El estudiante {inscripcion.usuario.get_full_name() or inscripcion.usuario.username} ({inscripcion.usuario.email}) "
        f"ha solicitado inscribirse en el curso '{inscripcion.curso.titulo}'.\n\n"
        f"Por favor, ingresa al panel de administración de ClubsHub para aprobar o rechazar la solicitud.\n\n"
        f"Saludos,\n"
        f"Equipo de ClubsHub"
    )
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, destinatarios, fail_silently=True)
    except Exception as e:
        print(f"Error al enviar correo de inscripción pendiente: {e}")

def enviar_correo_inscripcion_aprobada(inscripcion):
    """Notifica al estudiante que su inscripción fue aprobada."""
    if not inscripcion.usuario.email:
        return
    subject = f"¡Inscripción aprobada! - {inscripcion.curso.titulo}"
    message = (
        f"¡Hola {inscripcion.usuario.first_name or inscripcion.usuario.username}!\n\n"
        f"Tu solicitud de inscripción para el curso '{inscripcion.curso.titulo}' ha sido aprobada por un administrador.\n\n"
        f"Ya puedes acceder a la plataforma y comenzar a ver los módulos y videos del curso.\n\n"
        f"¡Mucho éxito!\n\n"
        f"Saludos,\n"
        f"Equipo de ClubsHub"
    )
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [inscripcion.usuario.email], fail_silently=True)
    except Exception as e:
        print(f"Error al enviar correo de inscripción aprobada: {e}")

def enviar_correo_actividad_entregada(progreso):
    """Notifica a los admins que un estudiante entregó una actividad."""
    from .models import Usuario
    admins = Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR).exclude(email='')
    destinatarios = [admin.email for admin in admins]
    if not destinatarios:
        destinatarios = [settings.DEFAULT_FROM_EMAIL]
        
    subject = f"Actividad en revisión: {progreso.modulo.titulo}"
    message = (
        f"Hola,\n\n"
        f"El estudiante {progreso.usuario.get_full_name() or progreso.usuario.username} ha enviado la actividad "
        f"'{progreso.modulo.titulo}' del curso '{progreso.modulo.curso.titulo}' para su revisión.\n\n"
        f"Por favor, ingresa al panel de administración de ClubsHub para revisar y calificar la entrega.\n\n"
        f"Saludos,\n"
        f"Equipo de ClubsHub"
    )
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, destinatarios, fail_silently=True)
    except Exception as e:
        print(f"Error al enviar correo de actividad entregada: {e}")

def enviar_correo_actividad_calificada(progreso):
    """Notifica al estudiante que su actividad fue calificada."""
    if not progreso.usuario.email:
        return
        
    estado_display = "Aprobada" if progreso.estado == "aprobado" else "Calificada"
    subject = f"Actividad {estado_display}: {progreso.modulo.titulo}"
    
    nota_str = f"Calificación: {progreso.calificacion}\n" if progreso.calificacion else ""
    retro_str = f"Comentarios del administrador:\n\"{progreso.retroalimentacion}\"\n" if progreso.retroalimentacion else ""
    
    message = (
        f"¡Hola {progreso.usuario.first_name or progreso.usuario.username}!\n\n"
        f"Tu actividad '{progreso.modulo.titulo}' del curso '{progreso.modulo.curso.titulo}' ha sido revisada "
        f"por el administrador y marcada como '{progreso.get_estado_display()}'.\n\n"
        f"{nota_str}"
        f"{retro_str}\n"
        f"Ingresa a la plataforma para ver más detalles.\n\n"
        f"Saludos,\n"
        f"Equipo de ClubsHub"
    )
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [progreso.usuario.email], fail_silently=True)
    except Exception as e:
        print(f"Error al enviar correo de actividad calificada: {e}")

def get_pending_enrollments_count(request):
    """Retorna la cantidad de inscripciones pendientes para el badge dinámico del sidebar."""
    from .models import Inscripcion
    return Inscripcion.objects.filter(aprobado_por_admin=False).count()

def get_review_requests_count(request):
    """Retorna la cantidad de tareas/módulos en revisión para el badge dinámico del sidebar."""
    from .models import ProgresoModulo
    return ProgresoModulo.objects.filter(estado="en_revision").count()

def dashboard_callback(request, context):
    """Inyecta estadísticas del panel al dashboard administrativo de Django Unfold."""
    from .models import Usuario, Curso, Inscripcion, ProgresoModulo
    
    # KPIs
    total_estudiantes = Usuario.objects.filter(rol=Usuario.Rol.ESTANDAR).count()
    total_cursos = Curso.objects.count()
    inscripciones_pendientes = Inscripcion.objects.filter(aprobado_por_admin=False).count()
    entregas_pendientes = ProgresoModulo.objects.filter(estado=ProgresoModulo.Estado.EN_REVISION).count()
    
    # Actividades en revisión recientes
    recientes_revision = ProgresoModulo.objects.filter(
        estado=ProgresoModulo.Estado.EN_REVISION
    ).order_by('-fecha_actualizacion')[:5]
    
    context.update({
        'kpi_estudiantes': total_estudiantes,
        'kpi_cursos': total_cursos,
        'kpi_inscripciones_pendientes': inscripciones_pendientes,
        'kpi_entregas_pendientes': entregas_pendientes,
        'recientes_revision': recientes_revision,
    })
    return context
