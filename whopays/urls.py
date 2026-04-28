from django.urls import path
from . import api_views, views
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='groups', permanent=False)),

    path('auth/signup/', views.SignUpView.as_view(), name='signup'),
    path('auth/login/', views.LogInView.as_view(), name='login'),
    path('auth/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('auth/password-reset/', views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('auth/password-reset/done/', views.CustomPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('auth/password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('auth/password-reset/complete/',
         views.CustomPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    path('account/', views.EditUserView.as_view(), name='account'),
    path('account/delete/', views.DeleteUserView.as_view(), name='account-delete'),

    path('groups/', views.GroupsView.as_view(), name='groups'),
    path('groups/create/', views.CreateNewGroupView.as_view(), name='group-create'),
    path('groups/join/', views.JoinExistingGroupView.as_view(), name='group-join'),

    path('groups/<str:code>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('groups/<str:code>/edit/', views.EditGroupView.as_view(), name='group-edit'),
    path('groups/<str:code>/leave/', views.LeaveGroupView.as_view(), name='group-leave'),
    path('groups/<str:code>/delete/', views.DeleteGroupView.as_view(), name='group-delete'),

    path('api/groups/<str:code>/advance-turn/', api_views.AdvanceTurnAPIView.as_view(), name='api-group-advance-turn'),
    path('api/groups/<str:code>/set-current-payer/', api_views.SetCurrentPayingMember.as_view(), name="api-group-set-current-payer"
    ),
    path('api/groups/<str:code>/reorder/', api_views.ReorderQueueAPIView.as_view(), name='api-group-reorder'),

    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/theme/', views.UpdateThemeColorView.as_view(), name="theme-update"),

]
