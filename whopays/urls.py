from django.urls import path

from . import views

urlpatterns = [
    path('group/<str:code>/reorder/', views.ReorderQueueAPIView.as_view(), name='reorder_queue'),

]