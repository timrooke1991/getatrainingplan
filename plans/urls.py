from django.urls import path
from . import views

app_name = "plans"
urlpatterns = [
    # post views
    path("", views.index, name="home"),
    path("<int:id>", views.response_detail, name="response_detail"),
]
