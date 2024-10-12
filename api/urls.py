from django.urls import path
from .views import login_view, register_view, logout_view, home, user_files_view, extract_html_view, generate_report

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('', home, name='home'),
    path('user_files/', user_files_view, name='user_files'),
    path('extract_html/<int:file_id>/', extract_html_view, name='extract_html'),
    path('generate_report/<int:file_id>/', generate_report, name='generate_report'),
]
