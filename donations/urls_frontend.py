"""
Place at: donations/urls_frontend.py
Kept separate from donations/urls.py (which holds your DRF router/API routes)
so frontend pages live at the root, not nested under /api/.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views_frontend

urlpatterns = [
    path('', views_frontend.home_view, name='home'),
    path('restaurants/', views_frontend.restaurant_list_view, name='restaurant_list'),
    path('agents/', views_frontend.agent_list_view, name='agent_list'),
    path('ngos/', views_frontend.recipient_list_view, name='recipient_list'),

    path('signup/', views_frontend.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='donations/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('post-login/', views_frontend.post_login_redirect, name='post_login_redirect'),

    path('dashboard/', views_frontend.dashboard_view, name='dashboard'),
    path('donations/new/', views_frontend.donation_create_view, name='donation_create'),
    path('donations/<int:pk>/', views_frontend.donation_detail_view, name='donation_detail'),

    path('agent/signup/', views_frontend.agent_signup_view, name='agent_signup'),
    path('agent/dashboard/', views_frontend.agent_dashboard_view, name='agent_dashboard'),
    path('agent/donations/<int:pk>/update-status/', views_frontend.agent_update_status_view, name='agent_update_status'),

    path('recipient/signup/', views_frontend.recipient_signup_view, name='recipient_signup'),
    path('recipient/dashboard/', views_frontend.recipient_dashboard_view, name='recipient_dashboard'),
    path('recipient/donations/<int:pk>/claim/', views_frontend.recipient_claim_view, name='recipient_claim'),
]