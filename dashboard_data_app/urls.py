from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("upload/", views.upload_view, name="upload"),
    path("sales/add/", views.add_sales_view, name="add_sales"),
    path("performance/", views.performance_view, name="performance"),
    path("summary/", views.summary_view, name="summary"),
    path("", views.home_view, name="home"),
]
