# rural_sports/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home_view, name='home'),
    path('store/', include('store.urls')),
    path('booking/', include('booking.urls', namespace='booking')), # <-- ADDED THIS
    path('events/', include('events.urls')),
    path('accounts/', include('allauth.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)