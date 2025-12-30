from django.contrib import admin
from .models import Room, Player, Game, ScoreRecord


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'created_at', 'uma_1st', 'uma_2nd', 'uma_3rd', 'uma_4th', 'oka']
    readonly_fields = ['code', 'created_at']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'order']
    list_filter = ['room']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['game_number', 'room', 'created_at']
    list_filter = ['room']


@admin.register(ScoreRecord)
class ScoreRecordAdmin(admin.ModelAdmin):
    list_display = ['player', 'game', 'score', 'rank', 'points', 'chip_change']
    list_filter = ['game', 'rank']
