from django.urls import path
from . import views

urlpatterns = [
    # Públicas
    path('', views.home_view, name='home'),
    path('noticias/', views.noticias_view, name='noticias'),
    path('noticias/<int:pk>/', views.noticia_detalle_view, name='noticia_detalle'),
    path('cursos/', views.cursos_view, name='cursos'),
    path('cursos/<int:pk>/', views.curso_detalle_view, name='curso_detalle'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # Admin — Noticias
    path('noticias/crear/', views.noticia_crear_view, name='noticia_crear'),
    path('noticias/<int:pk>/editar/', views.noticia_editar_view, name='noticia_editar'),
    path('noticias/<int:pk>/eliminar/', views.noticia_eliminar_view, name='noticia_eliminar'),

    # Admin — Cursos
    path('cursos/crear/', views.curso_crear_view, name='curso_crear'),
    path('cursos/<int:pk>/editar/', views.curso_editar_view, name='curso_editar'),
    path('cursos/<int:pk>/eliminar/', views.curso_eliminar_view, name='curso_eliminar'),

    # Admin — Módulos
    path('cursos/<int:curso_pk>/modulo/crear/', views.modulo_crear_view, name='modulo_crear'),
    path('cursos/<int:curso_pk>/modulo/<int:modulo_pk>/editar/', views.modulo_editar_view, name='modulo_editar'),
    path('cursos/<int:curso_pk>/modulo/<int:modulo_pk>/eliminar/', views.modulo_eliminar_view, name='modulo_eliminar'),
]
