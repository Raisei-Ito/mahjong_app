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
        ('no', 'ノーレート'),
        ('ten1', 'テンイチ'),
        ('ten2', 'テンニ'),
        ('ten3', 'テンサン'),
        ('ten5', 'テンゴ'),
        ('pin', 'テンピン'),
        ('ryanpin', 'テンリャンピン'),
        ('upin', 'ウーピン'),
        ('dekapin', 'デカピン'),
        ('custom', 'カスタム'),
    ]
    
    SASHI_UMA_CHOICES = [
        ('5-10', '5-10 (1位+10, 2位+5, 3位-5, 4位-10)'),
        ('10-20', '10-20 (1位+20, 2位+10, 3位-10, 4位-20)'),
        ('10-30', '10-30 (1位+30, 2位+10, 3位-10, 4位-30)'),
        ('custom', 'カスタム'),
    ]
    
    code = models.CharField(max_length=6, unique=True, default=generate_room_code, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # サシウマ設定
    sashi_uma_type = models.CharField(max_length=10, choices=SASHI_UMA_CHOICES, default='5-10', verbose_name="サシウマタイプ")
    sashi_uma_1_2 = models.IntegerField(default=5, verbose_name="サシウマ1-2位（カスタム用）")
    sashi_uma_3_4 = models.IntegerField(default=10, verbose_name="サシウマ3-4位（カスタム用）")
    # レート設定
    rate_type = models.CharField(max_length=10, choices=RATE_CHOICES, default='ten5', verbose_name="レート")
    # 持ち点・返し点設定（個別に設定可能）
    starting_points = models.IntegerField(default=25000, verbose_name="持ち点")
    return_points = models.IntegerField(default=30000, verbose_name="返し点")
    # 互換性のため残す（レートタイプがcustomの時に使用）
    custom_return_points = models.IntegerField(default=30000, verbose_name="カスタム返し点")
    # チップ設定
    chip_point_rate = models.FloatField(default=1.0, verbose_name="チップ1枚あたりのポイント")
    # オカ設定（レートから自動計算されるが、互換性のため残す）
    oka = models.IntegerField(default=20, verbose_name="オカ")
    
    def _get_sashi_uma_values(self):
        """サシウマの値を取得（タイプに応じて）"""
        if self.sashi_uma_type == '5-10':
            return (5, 10)
        elif self.sashi_uma_type == '10-20':
            return (10, 20)
        elif self.sashi_uma_type == '10-30':
            return (10, 30)
        else:  # custom
            return (self.sashi_uma_1_2, self.sashi_uma_3_4)
    
    @property
    def effective_sashi_uma_1_2(self):
        """有効なサシウマ1-2位"""
        return self._get_sashi_uma_values()[0]
    
    @property
    def effective_sashi_uma_3_4(self):
        """有効なサシウマ3-4位"""
        return self._get_sashi_uma_values()[1]
    
    # ウマ計算（サシウマから計算）
    # サシウマ「5-10」: 1位+10, 2位+5, 3位-5, 4位-10
    # サシウマ「10-20」: 1位+20, 2位+10, 3位-10, 4位-20
    # サシウマ「10-30」: 1位+30, 2位+10, 3位-10, 4位-30
    @property
    def uma_1st(self):
        """1位ウマ（サシウマから計算）"""
        _, uma_3_4 = self._get_sashi_uma_values()
        # 1位 = uma_3_4
        return uma_3_4
    
    @property
    def uma_2nd(self):
        """2位ウマ（サシウマから計算）"""
        uma_1_2, _ = self._get_sashi_uma_values()
        # 2位 = uma_1_2
        return uma_1_2
    
    @property
    def uma_3rd(self):
        """3位ウマ（サシウマから計算）"""
        uma_1_2, _ = self._get_sashi_uma_values()
        # 3位 = -uma_1_2
        return -uma_1_2
    
    @property
    def uma_4th(self):
        """4位ウマ（サシウマから計算）"""
        _, uma_3_4 = self._get_sashi_uma_values()
        # 4位 = -uma_3_4
        return -uma_3_4
    
    @property
    def oka_points(self):
        """オカポイント（返し点と持ち点の差から計算）"""
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
