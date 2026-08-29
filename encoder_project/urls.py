from django.urls import path
from converter import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/inspect/', views.inspect_file, name='inspect_file'),
    path('api/convert/', views.convert_file, name='convert_file'),
    path('health/', views.health, name='health'),
]
