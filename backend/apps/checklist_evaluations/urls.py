from django.urls import path
from . import views

urlpatterns = [
    path('', views.EvaluationListView.as_view()),
    path('choices/', views.ChoicesView.as_view()),
    path('<int:pk>/', views.EvaluationDetailView.as_view()),
    path('<int:pk>/participants/', views.ParticipantListView.as_view()),
    path('<int:pk>/participants/<int:participant_id>/', views.ParticipantDetailView.as_view()),
    path('<int:pk>/start/', views.StartView.as_view()),
]
