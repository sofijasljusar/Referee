from django.urls import path
from . import api_views, views
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='groups', permanent=False)),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LogInView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('groups/', views.GroupsView.as_view(), name='groups'),
    path('group/<str:code>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('group/<str:code>/reorder/', api_views.ReorderQueueAPIView.as_view(), name='reorder_queue'),

]
