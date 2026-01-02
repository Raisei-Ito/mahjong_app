"""
24時間使用されていない部屋を削除する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mahjong.models import Room


class Command(BaseCommand):
    help = '24時間使用されていない部屋を削除します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='削除せずに、削除対象の部屋を表示するだけ',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 24時間前の時刻を計算
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        # 24時間使用されていない部屋を取得
        old_rooms = Room.objects.filter(last_used_at__lt=cutoff_time)
        
        count = old_rooms.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('削除対象の部屋はありません。')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'削除対象の部屋: {count}件')
            )
            for room in old_rooms:
                self.stdout.write(
                    f'  - 部屋コード: {room.code}, '
                    f'作成日時: {room.created_at}, '
                    f'最終使用: {room.last_used_at}'
                )
        else:
            # 部屋を削除（関連するPlayer、Game、ScoreRecordも自動削除される）
            deleted_count = 0
            for room in old_rooms:
                room_code = room.code
                room.delete()
                deleted_count += 1
                self.stdout.write(
                    f'削除: 部屋コード {room_code}'
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'合計 {deleted_count} 件の部屋を削除しました。'
                )
            )

