from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegistroRefeicaoViewSet

router = DefaultRouter()
router.register(r'registros', RegistroRefeicaoViewSet,basename='registrorefeicao')
urlpatterns = [
    path('', include(router.urls)),
]
