from django.urls import path

from . import api_views, views

urlpatterns = [
    path('group/<str:code>/reorder/', api_views.ReorderQueueAPIView.as_view(), name='reorder_queue'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('groups/', views.GroupsView.as_view(), name='groups'),

]