from django.db import models
import string
import random


def generate_room_code():
    """6桁の英数字コードを生成"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))


class Room(models.Model):
    """部屋モデル"""
    RATE_CHOICES = [
        ('no', 'ノーレート (25000/25000)'),
        ('ten1', 'テンイチ (25000/26000)'),
        ('ten2', 'テンニ (25000/27000)'),
        ('ten3', 'テンサン (25000/28000)'),
        ('ten5', 'テンゴ (25000/30000)'),
        ('pin', 'テンピン (25000/35000)'),
        ('ryanpin', 'テンリャンピン (25000/45000)'),
        ('upin', 'ウーピン (25000/75000)'),
        ('dekapin', 'デカピン (25000/125000)'),
        ('custom', 'カスタム'),
    ]
    
    code = models.CharField(max_length=6, unique=True, default=generate_room_code, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # サシウマ設定
    sashi_uma_1_2 = models.IntegerField(default=5, verbose_name="サシウマ1-2位")
    sashi_uma_3_4 = models.IntegerField(default=10, verbose_name="サシウマ3-4位")
    # レート設定
    rate_type = models.CharField(max_length=10, choices=RATE_CHOICES, default='ten5', verbose_name="レート")
    custom_return_points = models.IntegerField(default=30000, verbose_name="カスタム返し点")
    # 持ち点設定
    starting_points = models.IntegerField(default=25000, verbose_name="持ち点")
    # オカ設定（レートから自動計算されるが、互換性のため残す）
    oka = models.IntegerField(default=20, verbose_name="オカ")
    
    # 互換性のためのプロパティ（既存のウマ設定）
    @property
    def uma_1st(self):
        """1位ウマ（サシウマから計算）"""
        return self.sashi_uma_1_2 + self.sashi_uma_3_4
    
    @property
    def uma_2nd(self):
        """2位ウマ（サシウマから計算）"""
        return self.sashi_uma_1_2
    
    @property
    def uma_3rd(self):
        """3位ウマ（サシウマから計算）"""
        return -self.sashi_uma_1_2
    
    @property
    def uma_4th(self):
        """4位ウマ（サシウマから計算）"""
        return -(self.sashi_uma_1_2 + self.sashi_uma_3_4)
    
    @property
    def return_points(self):
        """返し点（レートから計算）"""
        rate_map = {
            'no': 25000,        # ノーレート
            'ten1': 26000,      # テンイチ
            'ten2': 27000,     # テンニ
            'ten3': 28000,     # テンサン
            'ten5': 30000,     # テンゴ
            'pin': 35000,      # テンピン
            'ryanpin': 45000,  # テンリャンピン
            'upin': 75000,     # ウーピン
            'dekapin': 125000, # デカピン
        }
        return rate_map.get(self.rate_type, self.custom_return_points)
    
    @property
    def oka_points(self):
        """オカポイント（レートから計算）"""
        if self.rate_type == 'no':
            return 0
        elif self.rate_type == 'custom':
            diff = self.return_points - self.starting_points
            return diff // 1000 if diff > 0 else 0
        else:
            # 返し点と持ち点の差を1000で割った値がオカポイント
            diff = self.return_points - self.starting_points
            return diff // 1000 if diff > 0 else 0

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code}"


class Player(models.Model):
    """プレイヤーモデル"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50, verbose_name="プレイヤー名")
    order = models.IntegerField(verbose_name="順番")  # 1, 2, 3, 4

    class Meta:
        unique_together = [['room', 'order']]
        ordering = ['order']

    def __str__(self):
        return f"{self.name} (Room: {self.room.code})"


class Game(models.Model):
    """半荘（ゲーム）モデル"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='games')
    game_number = models.IntegerField(verbose_name="ゲーム番号", default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['room', 'game_number']]

    def __str__(self):
        return f"Game {self.game_number} (Room: {self.room.code})"


class ScoreRecord(models.Model):
    """スコア記録モデル"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='score_records')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='score_records')
    score = models.IntegerField(verbose_name="持ち点")
    chip_change = models.IntegerField(default=0, verbose_name="チップ増減")
    rank = models.IntegerField(null=True, blank=True, verbose_name="順位")  # 1, 2, 3, 4
    points = models.FloatField(null=True, blank=True, verbose_name="ポイント")

    class Meta:
        ordering = ['rank', 'player__order']

    def __str__(self):
        return f"{self.player.name}: {self.score}点 (Rank: {self.rank}, Points: {self.points})"
