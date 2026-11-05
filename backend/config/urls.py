from django.contrib import admin
from django.urls import include, path
from .views import health

urlpatterns = [path("admin/", admin.site.urls), path("api/health/", health),
               path("api/reference-architectures/", include("apps.reference_architectures.urls")),
               path("api/auth/", include("apps.users.urls"))]
