from django.urls import path
from .views import LocalidadApiView

urlpatterns = [
    path('', LocalidadApiView.as_view(), name='localidades')
]