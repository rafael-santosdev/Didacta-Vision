from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('', include('didacta.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Produção: servir media (uploads) via Django quando não há nginx/CDN
    urlpatterns += [
        path(f'{settings.MEDIA_URL.strip("/")}/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]