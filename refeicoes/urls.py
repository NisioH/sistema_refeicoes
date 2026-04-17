from django.urls import path
from . import views

urlpatterns = [
    path('', views.painel_refeicoes, name='painel_refeicoes'),
    path('novo/', views.novo_registro, name='novo_registro'),
    path('editar/<int:id>', views.editar_registro, name='editar_registro'),
    path('deletar/<int:id>', views.excluir_registro, name='excluir_registro'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
]
