from django.contrib import admin
from django.urls import path, re_path, include
from . import settings
from django.conf.urls.static import static
from notifications import urls as notifications_urls


urlpatterns = [
    path('prometheus/', include('django_prometheus.urls')),
    path('api/', include('api.urls'), name='api'),
    path('api/mobile/', include('mobile_app.urls'), name='api_mobile'),
    path('admin/', admin.site.urls),
    re_path(r'^inbox/notifications/', include(notifications_urls, namespace='notifications')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    