# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from functools import wraps
from django.utils.html import strip_tags

from .models import Noticia, Curso, Modulo, Inscripcion, Carrusel, ProgresoModulo


# ─────────────────────────────────────────────
# DECORADOR: solo admins
# ─────────────────────────────────────────────
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.rol == 'administrador' or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# HOME (index.html)
# ─────────────────────────────────────────────
def home_view(request):
    """Página de inicio: últimas 3 noticias para el hero."""
    context = {
        'noticias': Noticia.objects.all()[:3],
        'cursos': Curso.objects.all()[:4],
        'carruseles': Carrusel.objects.filter(activo=True)
    }
    return render(request, 'index.html', context)


# ─────────────────────────────────────────────
# NOTICIAS
# ─────────────────────────────────────────────
def noticias_view(request):
    """Página con todas las noticias, con filtro de ordenamiento."""
    orden = request.GET.get('orden', 'recientes')
    if orden == 'vistas':
        noticias = Noticia.objects.all().order_by('-vistas', '-fecha_publicacion')
    else:
        noticias = Noticia.objects.all().order_by('-fecha_publicacion')
    context = {
        'noticias': noticias,
        'orden_actual': orden,
    }
    return render(request, 'noticias.html', context)


def noticia_detalle_view(request, pk):
    """Página de detalle individual de una noticia."""
    noticia = get_object_or_404(Noticia, pk=pk)
    # Incrementar vistas
    Noticia.objects.filter(pk=pk).update(vistas=F('vistas') + 1)
    noticia.refresh_from_db()
    context = {
        'noticia': noticia,
    }
    return render(request, 'noticia_detalle.html', context)


@admin_required
def noticia_crear_view(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        contenido = request.POST.get('contenido', '').strip()
        imagen = request.FILES.get('imagen_portada')
        if not titulo or not contenido:
            messages.error(request, 'El título y el contenido son obligatorios.')
        else:
            noticia = Noticia(titulo=titulo, contenido=contenido, autor=request.user)
            if imagen:
                noticia.imagen_portada = imagen
            noticia.save()
            
            if request.POST.get('agregar_carrusel'):
                Carrusel.objects.update_or_create(
                    noticia_vinculada=noticia,
                    defaults={
                        'titulo': noticia.titulo,
                        'subtitulo': strip_tags(noticia.contenido)[:150] + "...",
                        'imagen_fondo': noticia.imagen_portada.name if noticia.imagen_portada else None,
                        'texto_boton': "Leer Noticia",
                        'activo': True
                    }
                )
                
            messages.success(request, f'Noticia «{titulo}» publicada exitosamente.')
            return redirect('noticias')
    return render(request, 'noticia_form.html')


@admin_required
def noticia_editar_view(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    en_carrusel = Carrusel.objects.filter(noticia_vinculada=noticia).exists()
    if request.method == 'POST':
        noticia.titulo = request.POST.get('titulo', '').strip()
        noticia.contenido = request.POST.get('contenido', '').strip()
        if request.FILES.get('imagen_portada'):
            noticia.imagen_portada = request.FILES['imagen_portada']
        if request.POST.get('eliminar_imagen') and noticia.imagen_portada:
            noticia.imagen_portada.delete(save=False)
            noticia.imagen_portada = None
        noticia.save()
        
        if request.POST.get('agregar_carrusel'):
            Carrusel.objects.update_or_create(
                noticia_vinculada=noticia,
                defaults={
                    'titulo': noticia.titulo,
                    'subtitulo': strip_tags(noticia.contenido)[:150] + "...",
                    'imagen_fondo': noticia.imagen_portada.name if noticia.imagen_portada else None,
                    'texto_boton': "Leer Noticia",
                    'activo': True
                }
            )
        else:
            # Si desmarcó la casilla, eliminar del carrusel
            Carrusel.objects.filter(noticia_vinculada=noticia).delete()
            
        messages.success(request, 'Noticia actualizada correctamente.')
        return redirect('noticias')
    return render(request, 'noticia_form.html', {'noticia': noticia, 'en_carrusel': en_carrusel})


@admin_required
def noticia_eliminar_view(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        titulo = noticia.titulo
        noticia.delete()
        messages.success(request, f'Noticia «{titulo}» eliminada.')
    return redirect('noticias')


# ─────────────────────────────────────────────
# CURSOS
# ─────────────────────────────────────────────
def cursos_view(request):
    """Catálogo completo de cursos."""
    mis_cursos = []
    if request.user.is_authenticated:
        mis_cursos = list(Curso.objects.filter(
            inscripciones__usuario=request.user,
            inscripciones__aprobado_por_admin=True,
        ))
        # Calcular progreso para cada curso inscrito
        for c in mis_cursos:
            total_modulos = c.modulos.count()
            vistos = c.modulos.filter(progresos__usuario=request.user).count()
            c.porcentaje_progreso = int((vistos / total_modulos * 100)) if total_modulos > 0 else 0

    context = {
        'cursos': Curso.objects.all(),
        'mis_cursos': mis_cursos,
    }
    return render(request, 'cursos.html', context)


@admin_required
def curso_crear_view(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        imagen = request.FILES.get('imagen_portada')
        if not titulo or not descripcion:
            messages.error(request, 'El título y la descripción son obligatorios.')
        else:
            curso = Curso(titulo=titulo, descripcion=descripcion, autor=request.user)
            if imagen:
                curso.imagen_portada = imagen
            curso.save()
            
            if request.POST.get('agregar_carrusel'):
                Carrusel.objects.update_or_create(
                    curso_vinculado=curso,
                    defaults={
                        'titulo': curso.titulo,
                        'subtitulo': strip_tags(curso.descripcion)[:150] + "...",
                        'imagen_fondo': curso.imagen_portada.name if curso.imagen_portada else None,
                        'texto_boton': "Explorar Curso",
                        'activo': True
                    }
                )
                
            messages.success(request, f'Curso «{titulo}» creado. Ahora puedes agregarle módulos.')
            return redirect('curso_detalle', pk=curso.pk)
    return render(request, 'curso_form.html')


@admin_required
def curso_editar_view(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    en_carrusel = Carrusel.objects.filter(curso_vinculado=curso).exists()
    if request.method == 'POST':
        curso.titulo = request.POST.get('titulo', '').strip()
        curso.descripcion = request.POST.get('descripcion', '').strip()
        if request.FILES.get('imagen_portada'):
            curso.imagen_portada = request.FILES['imagen_portada']
        if request.POST.get('eliminar_imagen') and curso.imagen_portada:
            curso.imagen_portada.delete(save=False)
            curso.imagen_portada = None
        curso.save()
        
        if request.POST.get('agregar_carrusel'):
            Carrusel.objects.update_or_create(
                curso_vinculado=curso,
                defaults={
                    'titulo': curso.titulo,
                    'subtitulo': strip_tags(curso.descripcion)[:150] + "...",
                    'imagen_fondo': curso.imagen_portada.name if curso.imagen_portada else None,
                    'texto_boton': "Explorar Curso",
                    'activo': True
                }
            )
        else:
            # Si desmarcó la casilla, eliminar del carrusel
            Carrusel.objects.filter(curso_vinculado=curso).delete()
            
        messages.success(request, 'Curso actualizado correctamente.')
        return redirect('curso_detalle', pk=pk)
    return render(request, 'curso_form.html', {'curso': curso, 'en_carrusel': en_carrusel})


@admin_required
def curso_eliminar_view(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        titulo = curso.titulo
        curso.delete()
        messages.success(request, f'Curso «{titulo}» eliminado.')
    return redirect('cursos')


# ─────────────────────────────────────────────
# DETALLE DE CURSO
# ─────────────────────────────────────────────
@login_required(login_url='login')
def curso_detalle_view(request, pk):
    """Detalle de un curso con sus módulos (requiere login)."""
    curso = get_object_or_404(Curso, pk=pk)
    inscripcion = Inscripcion.objects.filter(usuario=request.user, curso=curso).first()
    
    tiene_acceso = False
    if request.user.is_superuser or request.user.rol == 'administrador':
        tiene_acceso = True
    elif inscripcion and inscripcion.aprobado_por_admin:
        tiene_acceso = True

    if request.method == 'POST' and not inscripcion and not tiene_acceso:
        Inscripcion.objects.create(usuario=request.user, curso=curso)
        messages.success(request, '¡Te has inscrito! Tu inscripción está pendiente de aprobación.')
        return redirect('curso_detalle', pk=pk)

    # Progreso del usuario en este curso
    modulos = curso.modulos.all()
    total_modulos = modulos.count()
    
    # We will pass a dictionary of {modulo_id: ProgresoModulo object} to the template 
    # to easily access status, grade, and feedback for evaluable modules, 
    # and to check completion for normal modules.
    modulos_completados_ids = set()
    porcentaje = 0

    if tiene_acceso and total_modulos > 0:
        progresos = ProgresoModulo.objects.filter(
            usuario=request.user,
            modulo__curso=curso
        )
        progresos_dict = {p.modulo_id: p for p in progresos}
        
        for modulo in modulos:
            modulo.progreso_obj = progresos_dict.get(modulo.id)
            if modulo.progreso_obj and modulo.progreso_obj.estado in [ProgresoModulo.Estado.COMPLETADO, ProgresoModulo.Estado.APROBADO, ProgresoModulo.Estado.CALIFICADO]:
                modulos_completados_ids.add(modulo.id)
        
        porcentaje = int((len(modulos_completados_ids) / total_modulos) * 100)

    context = {
        'curso': curso,
        'modulos': modulos,
        'inscripcion': inscripcion,
        'tiene_acceso': tiene_acceso,
        'progresos_dict': progresos_dict,
        'modulos_completados_ids': modulos_completados_ids,
        'total_modulos': total_modulos,
        'modulos_completados_count': len(modulos_completados_ids),
        'porcentaje': porcentaje,
    }
    return render(request, 'curso_detalle.html', context)


@login_required(login_url='login')
@require_POST
def toggle_modulo_completado(request, curso_pk, modulo_pk):
    """Marcar o desmarcar un módulo como completado (AJAX)."""
    curso = get_object_or_404(Curso, pk=curso_pk)
    modulo = get_object_or_404(Modulo, pk=modulo_pk, curso=curso)

    # Verificar acceso
    tiene_acceso = False
    if request.user.is_superuser or request.user.rol == 'administrador':
        tiene_acceso = True
    else:
        inscripcion = Inscripcion.objects.filter(
            usuario=request.user, curso=curso, aprobado_por_admin=True
        ).first()
        if inscripcion:
            tiene_acceso = True

    if not tiene_acceso:
        return JsonResponse({'error': 'Sin acceso'}, status=403)

    if modulo.es_evaluable:
        return JsonResponse({'error': 'No se puede marcar manualmente un módulo evaluable'}, status=400)

    # Toggle: si ya existe, eliminarlo; si no, crearlo con estado COMPLETADO
    progreso = ProgresoModulo.objects.filter(usuario=request.user, modulo=modulo).first()
    if progreso:
        progreso.delete()
        completado = False
    else:
        ProgresoModulo.objects.create(
            usuario=request.user, modulo=modulo, estado=ProgresoModulo.Estado.COMPLETADO
        )
        completado = True

    completados = 0
    progresos = ProgresoModulo.objects.filter(usuario=request.user, modulo__curso=curso)
    for p in progresos:
        if p.estado in [ProgresoModulo.Estado.COMPLETADO, ProgresoModulo.Estado.APROBADO, ProgresoModulo.Estado.CALIFICADO]:
            completados += 1
            
    porcentaje = int((completados / total) * 100) if total > 0 else 0

    return JsonResponse({
        'completado': completado,
        'completados': completados,
        'total': total,
        'porcentaje': porcentaje,
    })


# ─────────────────────────────────────────────
# MÓDULOS
# ─────────────────────────────────────────────
@admin_required
def modulo_crear_view(request, curso_pk):
    curso = get_object_or_404(Curso, pk=curso_pk)
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        orden = request.POST.get('orden', 0)
        es_evaluable = request.POST.get('es_evaluable') == 'on'
        archivo = request.FILES.get('archivo_adjunto')
        if not titulo:
            messages.error(request, 'El título del módulo es obligatorio.')
        else:
            modulo = Modulo(
                curso=curso, titulo=titulo, descripcion=descripcion,
                video_url=video_url or None, orden=orden, es_evaluable=es_evaluable
            )
            if archivo:
                modulo.archivo_adjunto = archivo
            modulo.save()
            messages.success(request, f'Módulo «{titulo}» agregado al curso.')
            return redirect('curso_detalle', pk=curso_pk)
    siguiente_orden = curso.modulos.count() + 1
    return render(request, 'modulo_form.html', {'curso': curso, 'siguiente_orden': siguiente_orden})


@admin_required
def modulo_editar_view(request, curso_pk, modulo_pk):
    curso = get_object_or_404(Curso, pk=curso_pk)
    modulo = get_object_or_404(Modulo, pk=modulo_pk, curso=curso)
    if request.method == 'POST':
        modulo.titulo = request.POST.get('titulo', '').strip()
        modulo.descripcion = request.POST.get('descripcion', '').strip()
        modulo.video_url = request.POST.get('video_url', '').strip() or None
        modulo.orden = request.POST.get('orden', modulo.orden)
        modulo.es_evaluable = request.POST.get('es_evaluable') == 'on'
        if request.FILES.get('archivo_adjunto'):
            modulo.archivo_adjunto = request.FILES['archivo_adjunto']
        if request.POST.get('eliminar_archivo') and modulo.archivo_adjunto:
            modulo.archivo_adjunto.delete(save=False)
            modulo.archivo_adjunto = None
        modulo.save()
        messages.success(request, 'Módulo actualizado correctamente.')
        return redirect('curso_detalle', pk=curso_pk)
    return render(request, 'modulo_form.html', {'curso': curso, 'modulo': modulo, 'siguiente_orden': modulo.orden})


@admin_required
def modulo_eliminar_view(request, curso_pk, modulo_pk):
    curso = get_object_or_404(Curso, pk=curso_pk)
    modulo = get_object_or_404(Modulo, pk=modulo_pk, curso=curso)
    if request.method == 'POST':
        modulo.delete()
        messages.success(request, 'Módulo eliminado.')
    return redirect('curso_detalle', pk=curso_pk)


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
def login_view(request):
    """Inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')
            return redirect(next_url if next_url else 'home')
        else:
            messages.error(request, 'Credenciales incorrectas. Verifica tu usuario y contraseña.')
    return render(request, 'login.html')


# ─────────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────────
def registro_view(request):
    """Registro de nuevo usuario (rol Estándar por defecto)."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        from .models import Usuario
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya está en uso.')
        elif Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese correo.')
        else:
            user = Usuario.objects.create_user(
                username=username, email=email,
                first_name=first_name, last_name=last_name,
                password=password1, rol=Usuario.Rol.ESTANDAR,
            )
            login(request, user)
            messages.success(request, f'¡Bienvenido/a, {first_name}!')
            return redirect('home')
    return render(request, 'registro.html')


# ─────────────────────────────────────────────
# RECUPERAR CONTRASEÑA
# ─────────────────────────────────────────────
# Se usa django.contrib.auth.urls para recuperación de contraseña


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('home')
