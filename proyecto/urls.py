from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        html_email_template_name='registration/password_reset_email.html',
        email_template_name='registration/password_reset_email.txt'
    ), name='password_reset'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
