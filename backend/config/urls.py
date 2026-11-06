from django.contrib import admin
from django.urls import include, path
from .views import health
from apps.reference_architectures.views import ElementTypeListView

urlpatterns = [path("api/architectural-element-types/", ElementTypeListView.as_view()), path("admin/", admin.site.urls), path("api/health/", health),
               path("api/reference-architectures/", include("apps.reference_architectures.urls")),
               path("api/auth/", include("apps.users.urls"))]
