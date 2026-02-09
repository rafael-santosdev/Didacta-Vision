from django.urls import path
from . import views

app_name = 'didacta'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('verify-code/', views.verify_code_view, name='verify_code'),
    path('verify-code/cancel/', views.cancel_verification_view, name='cancel_verification'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
    path('films/<int:pk>/', views.film_detail, name='film_detail'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('admin/films/', views.film_list_admin, name='film_list_admin'),
    path('admin/films/create/', views.FilmCreateView.as_view(), name='film_create'),
    path('admin/films/<int:pk>/edit/', views.FilmUpdateView.as_view(), name='film_update'),
    path('admin/films/<int:pk>/delete/', views.FilmDeleteView.as_view(), name='film_delete'),
    path('admin/sessions/', views.session_list_admin, name='session_list_admin'),
    path('admin/sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('admin/sessions/<int:pk>/', views.session_detail_admin, name='session_detail_admin'),
    path('admin/sessions/<int:pk>/edit/', views.SessionUpdateView.as_view(), name='session_update'),
    path('admin/sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/<int:session_id>/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/cancel/', views.reservation_cancel, name='reservation_cancel'),
    path('admin/presence/<int:reservation_id>/', views.mark_presence, name='mark_presence'),
    path('films/<int:film_id>/comment/', views.forum_comment_create, name='forum_comment_create'),
    path('forum/comments/<int:pk>/delete/', views.forum_comment_delete, name='forum_comment_delete'),
    path('support/', views.help_ticket_create, name='help_ticket_create'),
    path('support/tickets/', views.help_ticket_list, name='help_ticket_list'),
    path('support/tickets/<int:pk>/', views.help_ticket_detail, name='help_ticket_detail'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    # AJAX para sessões vinculadas a filmes (admin custom)
    path('admin/films/sessions/<int:pk>/delete/', views.ajax_session_delete, name='ajax_session_delete'),
    path('admin/films/sessions/<int:pk>/edit/', views.ajax_session_edit, name='ajax_session_edit'),
]
