from django.urls import path
from .views import ArchitectureListView, ArchitectureDetailView, VersionListView, VersionDetailView, ElementListView, ElementDetailView

urlpatterns = [
    path('<int:pk>/versions/<int:version_id>/elements/', ElementListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/elements/<int:element_id>/', ElementDetailView.as_view()),
    path('', ArchitectureListView.as_view()),
    path('<int:pk>/', ArchitectureDetailView.as_view()),
    path('<int:pk>/versions/', VersionListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/', VersionDetailView.as_view()),
]
