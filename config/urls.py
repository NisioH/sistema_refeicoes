from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('painel-gerencial-secreto/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='refeicoes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('painel/', include('refeicoes.urls')),
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='raiz'),
]
