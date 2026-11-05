from django.urls import path
from .views import ArchitectureListView, ArchitectureDetailView, VersionListView, VersionDetailView

urlpatterns = [
    path('', ArchitectureListView.as_view()),
    path('<int:pk>/', ArchitectureDetailView.as_view()),
    path('<int:pk>/versions/', VersionListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/', VersionDetailView.as_view()),
]
