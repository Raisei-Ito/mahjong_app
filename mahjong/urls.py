from django.urls import path
from . import views

app_name = 'mahjong'

urlpatterns = [
    path('', views.index, name='index'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<str:room_code>/setup/', views.room_setup, name='room_setup'),
    path('room/<str:room_code>/record-score/', views.record_score, name='record_score'),
    path('room/<str:room_code>/dashboard/', views.room_dashboard, name='room_dashboard'),
    path('room/<str:room_code>/game-list-partial/', views.game_list_partial, name='game_list_partial'),
    path('room/<str:room_code>/delete-game/<int:game_id>/', views.delete_game, name='delete_game'),
    path('room/<str:room_code>/delete-room/', views.delete_room, name='delete_room'),
    path('room/<str:room_code>/edit-players/', views.edit_players, name='edit_players'),
    path('room/<str:room_code>/settings/', views.room_settings, name='room_settings'),
]

