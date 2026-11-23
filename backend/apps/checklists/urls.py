from django.urls import path
from . import views

urlpatterns = [
    path('derive/', views.DeriveChecklistView.as_view()),
    path('', views.ChecklistListView.as_view()),
    path('<int:pk>/', views.ChecklistDetailView.as_view()),
    path('<int:pk>/versions/', views.VersionListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/', views.VersionDetailView.as_view()),
    path('<int:pk>/versions/<int:version_id>/sections/', views.SectionListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/sections/reorder/', views.SectionReorderView.as_view()),
    path('<int:pk>/versions/<int:version_id>/sections/<int:item_id>/', views.SectionDetailView.as_view()),
    path('<int:pk>/versions/<int:version_id>/stakeholders/', views.StakeholderListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/stakeholders/<int:item_id>/', views.StakeholderDetailView.as_view()),
    path('<int:pk>/versions/<int:version_id>/questions/', views.QuestionListView.as_view()),
    path('<int:pk>/versions/<int:version_id>/questions/reorder/', views.QuestionReorderView.as_view()),
    path('<int:pk>/versions/<int:version_id>/questions/<int:item_id>/', views.QuestionDetailView.as_view()),
]
