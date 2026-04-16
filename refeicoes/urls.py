from django.urls import path
from . import views

urlpatterns = [
    path('', views.painel_refeicoes, name='painel_refeicoes'),
]
