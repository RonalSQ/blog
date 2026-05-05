from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from django.utils.html import strip_tags

from .models import Noticia, Curso, Modulo, Inscripcion, Carrusel


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
    """Página con todas las noticias."""
    context = {'noticias': Noticia.objects.all()}
    return render(request, 'noticias.html', context)


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
                        'imagen_fondo': noticia.imagen_portada if noticia.imagen_portada else None,
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
                    'imagen_fondo': noticia.imagen_portada if noticia.imagen_portada else None,
                    'texto_boton': "Leer Noticia",
                    'activo': True
                }
            )
            
        messages.success(request, 'Noticia actualizada correctamente.')
        return redirect('noticias')
    return render(request, 'noticia_form.html', {'noticia': noticia})


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
        mis_cursos = Curso.objects.filter(
            inscripciones__usuario=request.user,
            inscripciones__aprobado_por_admin=True,
        )
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
                        'imagen_fondo': curso.imagen_portada if curso.imagen_portada else None,
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
                    'imagen_fondo': curso.imagen_portada if curso.imagen_portada else None,
                    'texto_boton': "Explorar Curso",
                    'activo': True
                }
            )
            
        messages.success(request, 'Curso actualizado correctamente.')
        return redirect('curso_detalle', pk=pk)
    return render(request, 'curso_form.html', {'curso': curso})


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
    if request.method == 'POST' and not inscripcion:
        Inscripcion.objects.create(usuario=request.user, curso=curso)
        messages.success(request, '¡Te has inscrito! Tu inscripción está pendiente de aprobación.')
        return redirect('curso_detalle', pk=pk)
    context = {
        'curso': curso,
        'modulos': curso.modulos.all(),
        'inscripcion': inscripcion,
    }
    return render(request, 'curso_detalle.html', context)


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
        archivo = request.FILES.get('archivo_adjunto')
        if not titulo:
            messages.error(request, 'El título del módulo es obligatorio.')
        else:
            modulo = Modulo(
                curso=curso, titulo=titulo, descripcion=descripcion,
                video_url=video_url or None, orden=orden,
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
            return redirect(request.POST.get('next', 'home'))
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
