"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from loja.sitemaps import ProdutoSitemap, StaticViewSitemap

# Restringir o Django Admin apenas a superusers (Administradores).
# Gerentes (is_staff=True mas sem is_superuser) não podem aceder ao /gestao/admin/.
admin.site.has_permission = lambda request: bool(
    request.user.is_active and request.user.is_superuser
)

sitemaps = {
    'produtos': ProdutoSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('gestao/admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    path('', include('loja.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
