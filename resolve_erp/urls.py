from django.contrib import admin
from django.urls import path, re_path, include
from . import settings
from django.conf.urls.static import static
from notifications import urls as notifications_urls


urlpatterns = [
    path('api/', include('api.urls'), name='api'),
    path('api/m/', include('mobile_app.urls'), name='api_mobile'),
    path('', admin.site.urls),
    re_path(r'^inbox/notifications/', include(notifications_urls, namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)