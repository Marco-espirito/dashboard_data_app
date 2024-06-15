from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('upload/', views.upload_view, name='upload'),
    path('add_sales/', views.add_sales_view, name='add_sales'),
    path('performance/', views.performance_view, name='performance'),
    path('summary/', views.summary_view, name='summary'),
    path('', views.home_view, name='home'),  # Rediriger vers la page d'accueil
]
