from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# App Name for name spacing 
app_name = 'workers'  # accessible: workers:path_name --> workers:register 

urlpatterns = [
    path('accounts/register/', views.register, name='register'),
    path('accounts/clogin/', views.custom_login, name='custom_login'),
    path('accounts/profile/<int:user_id>', views.profile, name='profile'),
    path('accounts/profile/<int:user_id>/delete/', views.del_profile, name='profile_delete'),
    path('accounts/clogout/', views.custom_logout, name='custom_logout'),
    # path('accounts/forgot_password/', views.forgot_password, name='forgot_password'),
    path('accounts/password-reset/', views.EmailResetPassword.as_view(), name='password_reset'),
    # Confirmation token view from django 
    # uidb64 and token are url parameters so when we use {% url 'workers: password_reset_confirm' uid64=uid token=token%}
    path('accounts/password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # Password Complete Url 
    path('accounts/password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='workers/password_reset_complete.html'), name='password_reset_complete'),
]
