from django.contrib import admin
from django.urls import path
from . import views

app_name = 'user'
urlpatterns = [
    path('common/authentication/', views.common_authentication, name='common authentication'),
    path('common/verification/', views.common_verification, name='common verification'),
    path('server/useradd/', views.server_useradd, name='server useradd'),
    path('github/invitation/', views.github_invitation, name='github invitation'),
    path('', views.user_list, name='index'),
    path('add/', views.user_add, name='add'),
    path('edit/', views.user_edit, name='edit'),
    path('delete/', views.user_delete, name='delete'),
]
