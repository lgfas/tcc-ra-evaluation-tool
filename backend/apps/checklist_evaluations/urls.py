from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/progress/', views.ProgressView.as_view()),
    path('<int:pk>/complete/', views.CompleteView.as_view()),
    path('<int:pk>/results/', views.ResultsView.as_view()),
    path('<int:pk>/my-questions/', views.MyQuestionsView.as_view()),
    path('<int:pk>/my-answers/<int:question_id>/', views.MyAnswerView.as_view()),
    path('', views.EvaluationListView.as_view()),
    path('choices/', views.ChoicesView.as_view()),
    path('<int:pk>/', views.EvaluationDetailView.as_view()),
    path('<int:pk>/participants/', views.ParticipantListView.as_view()),
    path('<int:pk>/participants/<int:participant_id>/', views.ParticipantDetailView.as_view()),
    path('<int:pk>/start/', views.StartView.as_view()),
]
