from django.urls import path

from . import api_views, views

urlpatterns = [
    path('group/<str:code>/reorder/', api_views.ReorderQueueAPIView.as_view(), name='reorder_queue'),
    path('', views.SignupView.as_view(), name='signup'),

]