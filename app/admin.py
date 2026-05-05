from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import Usuario, Noticia, Curso, Modulo, Inscripcion


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

    # Agrega el campo 'rol' a los fieldsets de edición del usuario
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rol en ClubsHub', {'fields': ('rol',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rol en ClubsHub', {'fields': ('rol',)}),
    )


# ─────────────────────────────────────────────
# MÓDULO (inline dentro de Curso)
# ─────────────────────────────────────────────
class ModuloInline(TabularInline):
    model = Modulo
    extra = 1
    fields = ('orden', 'titulo', 'descripcion', 'archivo_adjunto', 'video_url')
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
