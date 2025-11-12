from django.urls import path

from . import api_views, views

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LogInView.as_view(), name='login'),
    path('groups/', views.GroupsView.as_view(), name='groups'),
    path('group/<str:code>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('group/<str:code>/reorder/', api_views.ReorderQueueAPIView.as_view(), name='reorder_queue'),

]
