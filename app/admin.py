from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import Usuario, Noticia, Curso, Modulo, Inscripcion, Carrusel, ProgresoModulo


# ─────────────────────────────────────────────
# USUARIO
# ─────────────────────────────────────────────
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin, ModelAdmin):
    """Panel de administración para el usuario personalizado."""
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('username', 'email', 'get_full_name', 'rol', 'is_active')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Agrega el campo 'rol' y 'foto_perfil' a los fieldsets de edición del usuario
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información de ClubsHub', {'fields': ('rol', 'foto_perfil')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información de ClubsHub', {'fields': ('rol', 'foto_perfil')}),
    )


# ─────────────────────────────────────────────
# MÓDULO (inline dentro de Curso)
# ─────────────────────────────────────────────
class ModuloInline(TabularInline):
    model = Modulo
    extra = 1
    fields = ('orden', 'titulo', 'descripcion', 'archivo_adjunto', 'video_url', 'video_url_2', 'video_url_3', 'es_evaluable', 'enlace_drive')
    ordering = ('orden',)


# ─────────────────────────────────────────────
# CURSO
# ─────────────────────────────────────────────
@admin.register(Curso)
class CursoAdmin(ModelAdmin):
    list_display = ('titulo', 'total_modulos', 'total_inscritos', 'fecha_creacion', 'autor')
    search_fields = ('titulo', 'descripcion')
    inlines = [ModuloInline]
    readonly_fields = ('autor',)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'autor', None) is None:
            obj.autor = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Módulos')
    def total_modulos(self, obj):
        return obj.modulos.count()

    @admin.display(description='Inscritos')
    def total_inscritos(self, obj):
        return obj.inscripciones.count()


# ─────────────────────────────────────────────
# NOTICIA
# ─────────────────────────────────────────────
@admin.register(Noticia)
class NoticiaAdmin(ModelAdmin):
    list_display = ('titulo', 'fecha_publicacion', 'autor')
    search_fields = ('titulo', 'contenido')
    list_filter = ('fecha_publicacion',)
    date_hierarchy = 'fecha_publicacion'
    readonly_fields = ('autor',)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'autor', None) is None:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
# INSCRIPCIÓN
# ─────────────────────────────────────────────
@admin.register(Inscripcion)
class InscripcionAdmin(ModelAdmin):
    list_display = ('usuario', 'curso', 'aprobado_por_admin', 'fecha_inscripcion')
    list_filter = ('aprobado_por_admin', 'curso')
    search_fields = ('usuario__username', 'usuario__email', 'curso__titulo')
    list_editable = ('aprobado_por_admin',)  # Aprobar desde la lista sin entrar al detalle
    date_hierarchy = 'fecha_inscripcion'
    ordering = ('-fecha_inscripcion',)


# ─────────────────────────────────────────────
# CARRUSEL
# ─────────────────────────────────────────────
@admin.register(Carrusel)
class CarruselAdmin(ModelAdmin):
    list_display = ('titulo', 'etiqueta', 'activo', 'orden')
    list_filter = ('activo',)
    search_fields = ('titulo', 'subtitulo', 'etiqueta')
    list_editable = ('activo', 'orden')
    ordering = ('orden', '-id')
    
    fieldsets = (
        ('Contenido Principal', {
            'fields': ('titulo', 'subtitulo', 'etiqueta', 'imagen_fondo')
        }),
        ('Enlaces (Selecciona solo uno)', {
            'fields': ('texto_boton', 'noticia_vinculada', 'curso_vinculado', 'enlace_url'),
            'description': 'El botón redirigirá a la noticia, al curso, o al enlace externo en ese orden de prioridad.'
        }),
        ('Configuración', {
            'fields': ('activo', 'orden')
        }),
    )


from django import forms

class ProgresoModuloAdminForm(forms.ModelForm):
    class Meta:
        model = ProgresoModulo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_states = [
            (ProgresoModulo.Estado.EN_REVISION, 'En Revisión'),
            (ProgresoModulo.Estado.CALIFICADO, 'Calificado'),
        ]
        if self.instance and self.instance.pk and self.instance.estado not in [ProgresoModulo.Estado.EN_REVISION, ProgresoModulo.Estado.CALIFICADO]:
            allowed_states.insert(0, (self.instance.estado, self.instance.get_estado_display()))
        self.fields['estado'].choices = allowed_states


# ─────────────────────────────────────────────
# PROGRESO DE MÓDULO (EVALUACIÓN)
# ─────────────────────────────────────────────
@admin.register(ProgresoModulo)
class ProgresoModuloAdmin(ModelAdmin):
    form = ProgresoModuloAdminForm
    list_display = ('usuario', 'modulo', 'estado', 'calificacion', 'fecha_actualizacion')
    list_filter = ('estado', 'modulo__curso', 'modulo')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'modulo__titulo')
    list_editable = ('estado', 'calificacion')
    ordering = ('-fecha_actualizacion',)
    
    fieldsets = (
        ('Información de Progreso', {
            'fields': ('usuario', 'modulo')
        }),
        ('Evaluación', {
            'fields': ('estado', 'calificacion', 'retroalimentacion')
        }),
    )
    readonly_fields = ('usuario', 'modulo')

    def has_add_permission(self, request):
        # Es preferible que se creen solos cuando el usuario avanza o mediante otra vía, 
        # pero permitimos agregar manualmente si es necesario.
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(modulo__es_evaluable=True)

    def get_changelist_form(self, request, **kwargs):
        kwargs['form'] = self.form
        return super().get_changelist_form(request, **kwargs)
