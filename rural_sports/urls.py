# rural_sports/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core import views as core_views

urlpatterns = [
    # ================= ADMIN =================
    path("admin/", admin.site.urls),

    # ================= CORE =================
    path("", core_views.home_view, name="home"),

    # ================= APPS =================
    path("store/", include("store.urls")),
    path("booking/", include("booking.urls", namespace="booking")),
    path("events/", include("events.urls")),

    # ================= AUTH (ALLAUTH) =================
    path("accounts/", include("allauth.urls")),

    # ================= PASSWORD RESET (EMAIL) =================
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]

# ================= STATIC / MEDIA =================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
