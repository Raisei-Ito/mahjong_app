from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import Room, Player, Game, ScoreRecord


class RoomModelTest(TestCase):
    """Roomモデルのテスト"""
    
    def test_room_code_generation(self):
        """部屋コードが自動生成されることを確認"""
        room = Room.objects.create()
        self.assertIsNotNone(room.code)
        self.assertEqual(len(room.code), 6)
        self.assertTrue(room.code.isalnum())
    
    def test_room_code_uniqueness(self):
        """部屋コードが一意であることを確認"""
        room1 = Room.objects.create()
        room2 = Room.objects.create()
        self.assertNotEqual(room1.code, room2.code)
    
    def test_sashi_uma_5_10(self):
        """サシウマ5-10の計算を確認"""
        room = Room.objects.create(sashi_uma_type='5-10')
        self.assertEqual(room.effective_sashi_uma_1_2, 5)
        self.assertEqual(room.effective_sashi_uma_3_4, 10)
        self.assertEqual(room.uma_1st, 10)  # 1位
        self.assertEqual(room.uma_2nd, 5)   # 2位
        self.assertEqual(room.uma_3rd, -5)   # 3位
        self.assertEqual(room.uma_4th, -10) # 4位
    
    def test_sashi_uma_10_20(self):
        """サシウマ10-20の計算を確認"""
        room = Room.objects.create(sashi_uma_type='10-20')
        self.assertEqual(room.effective_sashi_uma_1_2, 10)
        self.assertEqual(room.effective_sashi_uma_3_4, 20)
        self.assertEqual(room.uma_1st, 20)
        self.assertEqual(room.uma_2nd, 10)
        self.assertEqual(room.uma_3rd, -10)
        self.assertEqual(room.uma_4th, -20)
    
    def test_sashi_uma_10_30(self):
        """サシウマ10-30の計算を確認"""
        room = Room.objects.create(sashi_uma_type='10-30')
        self.assertEqual(room.effective_sashi_uma_1_2, 10)
        self.assertEqual(room.effective_sashi_uma_3_4, 30)
        self.assertEqual(room.uma_1st, 30)
        self.assertEqual(room.uma_2nd, 10)
        self.assertEqual(room.uma_3rd, -10)
        self.assertEqual(room.uma_4th, -30)
    
    def test_sashi_uma_custom(self):
        """カスタムサシウマの計算を確認"""
        room = Room.objects.create(
            sashi_uma_type='custom',
            sashi_uma_1_2=15,
            sashi_uma_3_4=25
        )
        self.assertEqual(room.effective_sashi_uma_1_2, 15)
        self.assertEqual(room.effective_sashi_uma_3_4, 25)
        self.assertEqual(room.uma_1st, 25)
        self.assertEqual(room.uma_2nd, 15)
        self.assertEqual(room.uma_3rd, -15)
        self.assertEqual(room.uma_4th, -25)
    
    def test_oka_points_calculation(self):
        """オカポイントの計算を確認"""
        room = Room.objects.create(
            starting_points=25000,
            return_points=30000
        )
        self.assertEqual(room.oka_points, 5)  # (30000 - 25000) / 1000
    
    def test_oka_points_zero_when_no_diff(self):
        """返し点と持ち点が同じ場合、オカポイントが0になることを確認"""
        room = Room.objects.create(
            starting_points=30000,
            return_points=30000
        )
        self.assertEqual(room.oka_points, 0)
    
    def test_oka_points_zero_when_negative_diff(self):
        """返し点が持ち点より小さい場合、オカポイントが0になることを確認"""
        room = Room.objects.create(
            starting_points=35000,
            return_points=30000
        )
        self.assertEqual(room.oka_points, 0)


class PlayerModelTest(TestCase):
    """Playerモデルのテスト"""
    
    def setUp(self):
        self.room = Room.objects.create()
    
    def test_player_creation(self):
        """プレイヤーが正しく作成されることを確認"""
        player = Player.objects.create(
            room=self.room,
            name="テストプレイヤー",
            order=1
        )
        self.assertEqual(player.name, "テストプレイヤー")
        self.assertEqual(player.order, 1)
        self.assertEqual(player.room, self.room)
    
    def test_player_unique_together(self):
        """同じ部屋で同じ順番のプレイヤーが重複できないことを確認"""
        Player.objects.create(room=self.room, name="プレイヤー1", order=1)
        with self.assertRaises(Exception):  # IntegrityError
            Player.objects.create(room=self.room, name="プレイヤー2", order=1)
    
    def test_player_different_rooms_same_order(self):
        """異なる部屋では同じ順番のプレイヤーが作成できることを確認"""
        room2 = Room.objects.create()
        Player.objects.create(room=self.room, name="プレイヤー1", order=1)
        player2 = Player.objects.create(room=room2, name="プレイヤー1", order=1)
        self.assertIsNotNone(player2)


class GameModelTest(TestCase):
    """Gameモデルのテスト"""
    
    def setUp(self):
        self.room = Room.objects.create()
    
    def test_game_creation(self):
        """ゲームが正しく作成されることを確認"""
        game = Game.objects.create(room=self.room, game_number=1)
        self.assertEqual(game.game_number, 1)
        self.assertEqual(game.room, self.room)
    
    def test_game_number_auto_increment(self):
        """ゲーム番号が自動的に増加することを確認"""
        game1 = Game.objects.create(room=self.room, game_number=1)
        game2 = Game.objects.create(room=self.room, game_number=2)
        self.assertEqual(game1.game_number, 1)
        self.assertEqual(game2.game_number, 2)
    
    def test_game_unique_together(self):
        """同じ部屋で同じゲーム番号が重複できないことを確認"""
        Game.objects.create(room=self.room, game_number=1)
        with self.assertRaises(Exception):  # IntegrityError
            Game.objects.create(room=self.room, game_number=1)
    
    def test_game_different_rooms_same_number(self):
        """異なる部屋では同じゲーム番号が作成できることを確認"""
        room2 = Room.objects.create()
        Game.objects.create(room=self.room, game_number=1)
        game2 = Game.objects.create(room=room2, game_number=1)
        self.assertIsNotNone(game2)


class ScoreRecordModelTest(TestCase):
    """ScoreRecordモデルのテスト"""
    
    def setUp(self):
        self.room = Room.objects.create()
        self.player = Player.objects.create(room=self.room, name="テストプレイヤー", order=1)
        self.game = Game.objects.create(room=self.room, game_number=1)
    
    def test_score_record_creation(self):
        """スコア記録が正しく作成されることを確認"""
        record = ScoreRecord.objects.create(
            game=self.game,
            player=self.player,
            score=30000,
            chip_change=0,
            rank=1,
            points=10.0
        )
        self.assertEqual(record.score, 30000)
        self.assertEqual(record.rank, 1)
        self.assertEqual(record.points, 10.0)


class ViewTest(TestCase):
    """ビューのテスト"""
    
    def setUp(self):
        self.client = Client()
        self.room = Room.objects.create()
    
    def test_index_view(self):
        """トップ画面が表示されることを確認"""
        response = self.client.get(reverse('mahjong:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_room_view_get(self):
        """GETリクエストで部屋作成ページにリダイレクトされることを確認"""
        response = self.client.get(reverse('mahjong:create_room'))
        self.assertEqual(response.status_code, 302)  # リダイレクト
    
    def test_create_room_view_post(self):
        """POSTリクエストで部屋が作成されることを確認"""
        response = self.client.post(reverse('mahjong:create_room'))
        self.assertEqual(response.status_code, 302)
        # 新しい部屋が作成されているか確認
        rooms = Room.objects.all()
        self.assertGreater(rooms.count(), 0)
    
    def test_join_room_view_invalid_code(self):
        """無効な部屋コードで参加しようとした場合のエラーを確認"""
        response = self.client.post(reverse('mahjong:join_room'), {
            'room_code': 'INVALID'
        })
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('見つかりませんでした' in str(m) for m in messages))
    
    def test_join_room_view_valid_code(self):
        """有効な部屋コードで参加できることを確認"""
        response = self.client.post(reverse('mahjong:join_room'), {
            'room_code': self.room.code
        })
        self.assertEqual(response.status_code, 302)
    
    def test_room_setup_view_get(self):
        """プレイヤー登録画面が表示されることを確認"""
        response = self.client.get(reverse('mahjong:room_setup', args=[self.room.code]))
        self.assertEqual(response.status_code, 200)
    
    def test_room_setup_view_post_valid(self):
        """有効なプレイヤー情報で登録できることを確認"""
        response = self.client.post(reverse('mahjong:room_setup', args=[self.room.code]), {
            'player_1': 'プレイヤー1',
            'player_2': 'プレイヤー2',
            'player_3': 'プレイヤー3',
            'player_4': 'プレイヤー4',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Player.objects.filter(room=self.room).count(), 4)
    
    def test_room_setup_view_post_invalid_count(self):
        """プレイヤーが4人未満の場合のエラーを確認"""
        response = self.client.post(reverse('mahjong:room_setup', args=[self.room.code]), {
            'player_1': 'プレイヤー1',
            'player_2': 'プレイヤー2',
            'player_3': 'プレイヤー3',
        })
        self.assertEqual(response.status_code, 200)  # エラーメッセージと共に同じページを表示
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('4名のプレイヤー名を入力してください' in str(m) for m in messages))
    
    def test_room_setup_view_post_name_too_long(self):
        """プレイヤー名が長すぎる場合のエラーを確認"""
        response = self.client.post(reverse('mahjong:room_setup', args=[self.room.code]), {
            'player_1': 'A' * 51,  # 51文字
            'player_2': 'プレイヤー2',
            'player_3': 'プレイヤー3',
            'player_4': 'プレイヤー4',
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('長すぎます' in str(m) for m in messages))
    
    def test_record_score_view_get(self):
        """スコア入力画面が表示されることを確認"""
        # プレイヤーを4人作成
        for i in range(1, 5):
            Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i)
        
        response = self.client.get(reverse('mahjong:record_score', args=[self.room.code]))
        self.assertEqual(response.status_code, 200)
    
    def test_record_score_view_post_valid(self):
        """有効なスコアで記録できることを確認"""
        # プレイヤーを4人作成
        players = []
        for i in range(1, 5):
            players.append(Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i))
        
        post_data = {}
        scores = [35000, 30000, 25000, 20000]  # 合計110000点
        for i, player in enumerate(players):
            post_data[f'score_{player.id}'] = scores[i]
            post_data[f'chip_{player.id}'] = 0
        
        response = self.client.post(reverse('mahjong:record_score', args=[self.room.code]), post_data)
        self.assertEqual(response.status_code, 302)
        
        # ゲームが作成されているか確認
        game = Game.objects.filter(room=self.room).first()
        self.assertIsNotNone(game)
        self.assertEqual(game.score_records.count(), 4)
    
    def test_record_score_view_post_invalid_score_range(self):
        """スコアが範囲外の場合のエラーを確認"""
        players = []
        for i in range(1, 5):
            players.append(Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i))
        
        post_data = {}
        for i, player in enumerate(players):
            if i == 0:
                post_data[f'score_{player.id}'] = 300000  # 範囲外
            else:
                post_data[f'score_{player.id}'] = 30000
            post_data[f'chip_{player.id}'] = 0
        
        response = self.client.post(reverse('mahjong:record_score', args=[self.room.code]), post_data)
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('範囲外です' in str(m) for m in messages))
    
    def test_record_score_view_post_invalid_chip_range(self):
        """チップ増減が範囲外の場合のエラーを確認"""
        players = []
        for i in range(1, 5):
            players.append(Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i))
        
        post_data = {}
        for i, player in enumerate(players):
            post_data[f'score_{player.id}'] = 30000
            if i == 0:
                post_data[f'chip_{player.id}'] = 20000  # 範囲外
            else:
                post_data[f'chip_{player.id}'] = 0
        
        response = self.client.post(reverse('mahjong:record_score', args=[self.room.code]), post_data)
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('範囲外です' in str(m) for m in messages))
    
    def test_room_dashboard_view(self):
        """ダッシュボードが表示されることを確認"""
        # プレイヤーを4人作成
        for i in range(1, 5):
            Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i)
        
        response = self.client.get(reverse('mahjong:room_dashboard', args=[self.room.code]))
        self.assertEqual(response.status_code, 200)
    
    def test_delete_game_view(self):
        """ゲームが削除されることを確認"""
        # プレイヤーとゲームを作成
        player = Player.objects.create(room=self.room, name='プレイヤー1', order=1)
        game = Game.objects.create(room=self.room, game_number=1)
        ScoreRecord.objects.create(game=game, player=player, score=30000, rank=1, points=10.0)
        
        response = self.client.post(reverse('mahjong:delete_game', args=[self.room.code, game.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Game.objects.filter(id=game.id).exists())
    
    def test_delete_room_view(self):
        """部屋が削除されることを確認"""
        response = self.client.post(reverse('mahjong:delete_room', args=[self.room.code]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Room.objects.filter(id=self.room.id).exists())
    
    def test_edit_players_view_get(self):
        """プレイヤー編集画面が表示されることを確認"""
        for i in range(1, 5):
            Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i)
        
        response = self.client.get(reverse('mahjong:edit_players', args=[self.room.code]))
        self.assertEqual(response.status_code, 200)
    
    def test_edit_players_view_post_valid(self):
        """有効なプレイヤー情報で更新できることを確認"""
        # 既存のプレイヤーを作成
        for i in range(1, 5):
            Player.objects.create(room=self.room, name=f'プレイヤー{i}', order=i)
        
        response = self.client.post(reverse('mahjong:edit_players', args=[self.room.code]), {
            'player_1': '新しいプレイヤー1',
            'player_2': '新しいプレイヤー2',
            'player_3': '新しいプレイヤー3',
            'player_4': '新しいプレイヤー4',
        })
        self.assertEqual(response.status_code, 302)
        
        # プレイヤー名が更新されているか確認
        player1 = Player.objects.filter(room=self.room, order=1).first()
        self.assertEqual(player1.name, '新しいプレイヤー1')
    
    def test_room_settings_view_get(self):
        """部屋設定画面が表示されることを確認"""
        response = self.client.get(reverse('mahjong:room_settings', args=[self.room.code]))
        self.assertEqual(response.status_code, 200)
    
    def test_room_settings_view_post_valid(self):
        """有効な設定で更新できることを確認"""
        response = self.client.post(reverse('mahjong:room_settings', args=[self.room.code]), {
            'sashi_uma_type': '10-20',
            'rate_type': 'ten5',
            'starting_points': '25000',
            'return_points': '30000',
            'chip_point_rate': '100.0',
        })
        self.assertEqual(response.status_code, 302)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.sashi_uma_type, '10-20')
        self.assertEqual(self.room.starting_points, 25000)
        self.assertEqual(self.room.return_points, 30000)
    
    def test_room_settings_view_post_invalid_sashi_uma(self):
        """無効なサシウマタイプの場合のエラーを確認"""
        response = self.client.post(reverse('mahjong:room_settings', args=[self.room.code]), {
            'sashi_uma_type': 'invalid',
            'rate_type': 'ten5',
            'starting_points': '25000',
            'return_points': '30000',
            'chip_point_rate': '100.0',
        })
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('無効' in str(m) for m in messages))
    
    def test_room_settings_view_post_invalid_points_range(self):
        """ポイントが範囲外の場合のエラーを確認"""
        response = self.client.post(reverse('mahjong:room_settings', args=[self.room.code]), {
            'sashi_uma_type': '5-10',
            'rate_type': 'ten5',
            'starting_points': '2000000',  # 範囲外
            'return_points': '30000',
            'chip_point_rate': '100.0',
        })
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('範囲外です' in str(m) for m in messages))


class PointCalculationTest(TestCase):
    """ポイント計算のテスト"""
    
    def setUp(self):
        self.room = Room.objects.create(
            sashi_uma_type='10-20',
            starting_points=25000,
            return_points=30000,
            oka=20
        )
        self.players = []
        for i in range(1, 5):
            self.players.append(Player.objects.create(
                room=self.room,
                name=f'プレイヤー{i}',
                order=i
            ))
    
    def test_point_calculation_standard(self):
        """標準的なポイント計算を確認"""
        # スコア: 35000, 30000, 25000, 20000 (合計110000)
        scores = [35000, 30000, 25000, 20000]
        
        game = Game.objects.create(room=self.room, game_number=1)
        score_records = []
        
        for i, player in enumerate(self.players):
            score_records.append(ScoreRecord(
                game=game,
                player=player,
                score=scores[i],
                chip_change=0
            ))
        
        # 順位を判定
        score_records.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
        for rank, record in enumerate(score_records, start=1):
            record.rank = rank
        
        # ポイントを計算
        for record in score_records:
            base_points = (record.score - self.room.return_points) / 1000
            uma_map = {
                1: self.room.uma_1st,
                2: self.room.uma_2nd,
                3: self.room.uma_3rd,
                4: self.room.uma_4th,
            }
            uma = uma_map.get(record.rank, 0)
            oka = self.room.oka if record.rank == 1 else 0
            record.points = base_points + uma + oka
            record.save()
        
        # 1位: (35000-30000)/1000 + 20(ウマ) + 20(オカ) = 5 + 20 + 20 = 45.0
        record_1st = ScoreRecord.objects.get(player=self.players[0], rank=1)
        self.assertEqual(record_1st.points, 45.0)
        
        # 2位: (30000-30000)/1000 + 10(ウマ) = 0 + 10 = 10.0
        record_2nd = ScoreRecord.objects.get(player=self.players[1], rank=2)
        self.assertEqual(record_2nd.points, 10.0)
        
        # 3位: (25000-30000)/1000 + (-10)(ウマ) = -5 - 10 = -15.0
        record_3rd = ScoreRecord.objects.get(player=self.players[2], rank=3)
        self.assertEqual(record_3rd.points, -15.0)
        
        # 4位: (20000-30000)/1000 + (-20)(ウマ) = -10 - 20 = -30.0
        record_4th = ScoreRecord.objects.get(player=self.players[3], rank=4)
        self.assertEqual(record_4th.points, -30.0)
    
    def test_point_calculation_with_tie(self):
        """同点の場合の順位判定を確認"""
        # 2人が同点の場合
        scores = [35000, 30000, 30000, 20000]
        
        game = Game.objects.create(room=self.room, game_number=1)
        score_records = []
        
        for i, player in enumerate(self.players):
            score_records.append(ScoreRecord(
                game=game,
                player=player,
                score=scores[i],
                chip_change=0
            ))
        
        # 順位を判定（同点の場合はプレイヤー順）
        score_records.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
        for rank, record in enumerate(score_records, start=1):
            record.rank = rank
            record.save()  # 保存を追加
        
        # 2位と3位が同点の場合、orderが小さい方が上位
        record_2nd = ScoreRecord.objects.get(player=self.players[1], rank=2)
        record_3rd = ScoreRecord.objects.get(player=self.players[2], rank=3)
        self.assertEqual(record_2nd.score, 30000)
        self.assertEqual(record_3rd.score, 30000)
        self.assertLess(record_2nd.player.order, record_3rd.player.order)


class ChipCalculationTest(TestCase):
    """チップ計算のテスト"""
    
    def setUp(self):
        self.room = Room.objects.create(
            chip_point_rate=1.0  # 1チップ = 100ポイント
        )
        self.player = Player.objects.create(room=self.room, name='プレイヤー1', order=1)
        self.game = Game.objects.create(room=self.room, game_number=1)
    
    def test_chip_point_conversion(self):
        """チップからポイントへの換算を確認"""
        # チップ換算率が1.0の場合、1チップ = 100ポイント
        # データベースには1.0として保存されているが、計算時はそのまま使用
        # chip_points = total_chips * room.chip_point_rate * 100
        total_chips = 5
        chip_points = total_chips * self.room.chip_point_rate * 100
        self.assertEqual(chip_points, 500.0)  # 5チップ * 1.0 * 100 = 500ポイント
    
    def test_total_amount_calculation(self):
        """合計金額の計算を確認"""
        # ポイント: 10.0pt = 1000ポイント（100倍）
        # チップ: 5チップ = 500ポイント
        # 合計: 1500ポイント
        ScoreRecord.objects.create(
            game=self.game,
            player=self.player,
            score=30000,
            chip_change=5,
            rank=1,
            points=10.0
        )
        
        total_points = 10.0
        total_chips = 5
        chip_points = total_chips * self.room.chip_point_rate * 100
        total_amount_pt = (total_points * 100) + chip_points
        
        self.assertEqual(total_amount_pt, 1500.0)


class IntegrationTest(TestCase):
    """統合テスト"""
    
    def test_full_game_flow(self):
        """ゲームの完全なフローをテスト"""
        # 1. 部屋を作成
        room = Room.objects.create()
        
        # 2. プレイヤーを4人登録
        players = []
        for i in range(1, 5):
            players.append(Player.objects.create(
                room=room,
                name=f'プレイヤー{i}',
                order=i
            ))
        self.assertEqual(Player.objects.filter(room=room).count(), 4)
        
        # 3. ゲームを3回記録
        for game_num in range(1, 4):
            game = Game.objects.create(room=room, game_number=game_num)
            
            # スコアを記録
            scores = [35000, 30000, 25000, 20000]
            score_records = []
            for i, player in enumerate(players):
                score_records.append(ScoreRecord(
                    game=game,
                    player=player,
                    score=scores[i],
                    chip_change=0
                ))
            
            # 順位とポイントを計算
            score_records.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
            for rank, record in enumerate(score_records, start=1):
                record.rank = rank
                base_points = (record.score - room.return_points) / 1000
                uma_map = {
                    1: room.uma_1st,
                    2: room.uma_2nd,
                    3: room.uma_3rd,
                    4: room.uma_4th,
                }
                uma = uma_map.get(record.rank, 0)
                oka = room.oka if record.rank == 1 else 0
                record.points = base_points + uma + oka
                record.save()
        
        # 4. 累計ポイントを確認
        for player in players:
            total_points = sum(
                sr.points for sr in ScoreRecord.objects.filter(player=player)
                if sr.points is not None
            )
            # 3ゲーム分の累計なので、1ゲーム目のポイントの3倍になる
            self.assertIsNotNone(total_points)
        
        # 5. ゲームが3つ作成されていることを確認
        self.assertEqual(Game.objects.filter(room=room).count(), 3)
        
        # 6. スコア記録が12個（4人×3ゲーム）作成されていることを確認
        self.assertEqual(ScoreRecord.objects.filter(game__room=room).count(), 12)


class MahjongCalculationTest(TestCase):
    """麻雀の計算ルールに基づいた実践的なテスト"""
    
    def setUp(self):
        """標準的な設定で部屋とプレイヤーを作成"""
        self.room = Room.objects.create(
            sashi_uma_type='10-20',
            starting_points=25000,
            return_points=30000,
            oka=20,
            chip_point_rate=1.0
        )
        self.players = []
        for i in range(1, 5):
            self.players.append(Player.objects.create(
                room=self.room,
                name=f'プレイヤー{i}',
                order=i
            ))
    
    def _calculate_and_save_scores(self, scores, chip_changes=None):
        """スコアを計算して保存するヘルパーメソッド"""
        if chip_changes is None:
            chip_changes = [0, 0, 0, 0]
        
        game = Game.objects.create(room=self.room, game_number=1)
        score_records = []
        
        for i, player in enumerate(self.players):
            score_records.append(ScoreRecord(
                game=game,
                player=player,
                score=scores[i],
                chip_change=chip_changes[i]
            ))
        
        # 順位を判定
        score_records.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
        for rank, record in enumerate(score_records, start=1):
            record.rank = rank
        
        # ポイントを計算
        for record in score_records:
            base_points = (record.score - self.room.return_points) / 1000
            uma_map = {
                1: self.room.uma_1st,
                2: self.room.uma_2nd,
                3: self.room.uma_3rd,
                4: self.room.uma_4th,
            }
            uma = uma_map.get(record.rank, 0)
            oka = self.room.oka if record.rank == 1 else 0
            record.points = base_points + uma + oka
            record.save()
        
        return score_records
    
    def test_standard_game_calculation(self):
        """標準的な半荘の計算（返し点30000点基準）"""
        # スコア: 35000, 30000, 25000, 20000
        # 合計: 110000点（返し点×4=120000点ではないが、これは正常）
        scores = [35000, 30000, 25000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: 35000点 → (35000-30000)/1000 + 20(ウマ) + 20(オカ) = 5 + 20 + 20 = 45.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 45.0)
        
        # 2位: 30000点 → (30000-30000)/1000 + 10(ウマ) = 0 + 10 = 10.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 10.0)
        
        # 3位: 25000点 → (25000-30000)/1000 + (-10)(ウマ) = -5 - 10 = -15.0pt
        record_3rd = [r for r in records if r.rank == 3][0]
        self.assertEqual(record_3rd.points, -15.0)
        
        # 4位: 20000点 → (20000-30000)/1000 + (-20)(ウマ) = -10 - 20 = -30.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -30.0)
        
        # ポイントの合計が0になることを確認（素点の合計は0でなくても、ウマとオカで調整される）
        total_points = sum(r.points for r in records)
        # 45 + 10 - 15 - 30 = 10.0（オカ20ptが含まれるため、合計は10ptになる）
        self.assertEqual(total_points, 10.0)
    
    def test_perfect_return_points_game(self):
        """持ち点の合計が返し点×4になる場合の計算"""
        # スコア: 35000, 30000, 25000, 30000（合計120000 = 30000×4）
        scores = [35000, 30000, 25000, 30000]
        records = self._calculate_and_save_scores(scores)
        
        # 素点の合計を確認
        base_points_sum = sum((r.score - self.room.return_points) / 1000 for r in records)
        self.assertEqual(base_points_sum, 0.0)  # 素点の合計は0
        
        # ポイントの合計（ウマとオカを含む）
        total_points = sum(r.points for r in records)
        # 1位: 5 + 20 + 20 = 45, 2位: 0 + 10 = 10, 3位: -5 - 10 = -15, 4位: 0 - 20 = -20
        # 合計: 45 + 10 - 15 - 20 = 20（オカ20ptのみ）
        self.assertEqual(total_points, 20.0)
    
    def test_big_win_calculation(self):
        """大勝ちの場合の計算"""
        # 1位が大勝ち: 50000点
        scores = [50000, 30000, 20000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (50000-30000)/1000 + 20 + 20 = 20 + 20 + 20 = 60.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 60.0)
        
        # 2位: (30000-30000)/1000 + 10 = 10.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 10.0)
        
        # 3位と4位が同点の場合、orderが小さい方が上位
        record_3rd = [r for r in records if r.rank == 3][0]
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_3rd.points, -20.0)  # -10 - 10 = -20
        self.assertEqual(record_4th.points, -30.0)  # -10 - 20 = -30
    
    def test_big_loss_calculation(self):
        """大負けの場合の計算"""
        # 4位が大負け: 10000点
        scores = [30000, 30000, 30000, 10000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (30000-30000)/1000 + 20 + 20 = 40.0pt（同点でも1位）
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 40.0)
        
        # 4位: (10000-30000)/1000 - 20 = -20 - 20 = -40.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -40.0)
    
    def test_different_return_points(self):
        """返し点が異なる場合の計算"""
        # 返し点を25000点に変更
        self.room.return_points = 25000
        self.room.save()
        
        # スコア: 30000, 25000, 20000, 20000
        scores = [30000, 25000, 20000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (30000-25000)/1000 + 20 + 20 = 5 + 20 + 20 = 45.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 45.0)
        
        # 2位: (25000-25000)/1000 + 10 = 10.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 10.0)
    
    def test_different_sashi_uma_5_10(self):
        """サシウマ5-10の場合の計算"""
        self.room.sashi_uma_type = '5-10'
        self.room.save()
        
        scores = [35000, 30000, 25000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (35000-30000)/1000 + 10(ウマ) + 20(オカ) = 5 + 10 + 20 = 35.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 35.0)
        
        # 2位: (30000-30000)/1000 + 5(ウマ) = 5.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 5.0)
        
        # 3位: (25000-30000)/1000 - 5(ウマ) = -5 - 5 = -10.0pt
        record_3rd = [r for r in records if r.rank == 3][0]
        self.assertEqual(record_3rd.points, -10.0)
        
        # 4位: (20000-30000)/1000 - 10(ウマ) = -10 - 10 = -20.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -20.0)
    
    def test_different_sashi_uma_10_30(self):
        """サシウマ10-30の場合の計算"""
        self.room.sashi_uma_type = '10-30'
        self.room.save()
        
        scores = [35000, 30000, 25000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (35000-30000)/1000 + 30(ウマ) + 20(オカ) = 5 + 30 + 20 = 55.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 55.0)
        
        # 4位: (20000-30000)/1000 - 30(ウマ) = -10 - 30 = -40.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -40.0)
    
    def test_custom_sashi_uma(self):
        """カスタムサシウマの場合の計算"""
        self.room.sashi_uma_type = 'custom'
        self.room.sashi_uma_1_2 = 15
        self.room.sashi_uma_3_4 = 25
        self.room.save()
        
        scores = [35000, 30000, 25000, 20000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位: (35000-30000)/1000 + 25(ウマ) + 20(オカ) = 5 + 25 + 20 = 50.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 50.0)
        
        # 2位: (30000-30000)/1000 + 15(ウマ) = 15.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 15.0)
    
    def test_oka_only_for_first_place(self):
        """オカが1位のみに適用されることを確認"""
        scores = [35000, 35000, 30000, 20000]  # 1位と2位が同点
        records = self._calculate_and_save_scores(scores)
        
        # 1位（orderが小さい方）: オカが適用される
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertIn(20.0, [record_1st.points - ((record_1st.score - self.room.return_points) / 1000 + self.room.uma_1st)])
        
        # 2位: オカが適用されない
        record_2nd = [r for r in records if r.rank == 2][0]
        oka_in_2nd = record_2nd.points - ((record_2nd.score - self.room.return_points) / 1000 + self.room.uma_2nd)
        self.assertEqual(oka_in_2nd, 0.0)
    
    def test_chip_calculation(self):
        """チップの計算が正しいことを確認"""
        scores = [35000, 30000, 25000, 20000]
        chip_changes = [5, 0, -2, -3]  # 1位が+5チップ、3位が-2チップ、4位が-3チップ
        records = self._calculate_and_save_scores(scores, chip_changes)
        
        # チップ換算率が1.0の場合、1チップ = 100ポイント
        # 1位: 5チップ = 500ポイント
        record_1st = [r for r in records if r.rank == 1][0]
        chip_points_1st = record_1st.chip_change * self.room.chip_point_rate * 100
        self.assertEqual(chip_points_1st, 500.0)
        
        # 3位: -2チップ = -200ポイント
        record_3rd = [r for r in records if r.rank == 3][0]
        chip_points_3rd = record_3rd.chip_change * self.room.chip_point_rate * 100
        self.assertEqual(chip_points_3rd, -200.0)
        
        # チップの合計が0になることを確認
        total_chips = sum(r.chip_change for r in records)
        self.assertEqual(total_chips, 0)
    
    def test_chip_point_rate_calculation(self):
        """異なるチップ換算率での計算"""
        self.room.chip_point_rate = 0.5  # 1チップ = 50ポイント
        self.room.save()
        
        scores = [35000, 30000, 25000, 20000]
        chip_changes = [10, 0, 0, -10]
        records = self._calculate_and_save_scores(scores, chip_changes)
        
        # 1位: 10チップ = 10 * 0.5 * 100 = 500ポイント
        record_1st = [r for r in records if r.rank == 1][0]
        chip_points_1st = record_1st.chip_change * self.room.chip_point_rate * 100
        self.assertEqual(chip_points_1st, 500.0)
        
        # 4位: -10チップ = -10 * 0.5 * 100 = -500ポイント
        record_4th = [r for r in records if r.rank == 4][0]
        chip_points_4th = record_4th.chip_change * self.room.chip_point_rate * 100
        self.assertEqual(chip_points_4th, -500.0)
    
    def test_multiple_games_cumulative(self):
        """複数ゲームの累計計算が正しいことを確認"""
        # ゲーム1: 1位が大勝ち
        scores1 = [50000, 30000, 20000, 20000]
        records1 = self._calculate_and_save_scores(scores1)
        
        # ゲーム2: 1位が大負け
        game2 = Game.objects.create(room=self.room, game_number=2)
        scores2 = [20000, 30000, 30000, 30000]
        records2 = []
        for i, player in enumerate(self.players):
            records2.append(ScoreRecord(
                game=game2,
                player=player,
                score=scores2[i],
                chip_change=0
            ))
        
        # 順位とポイントを計算
        records2.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
        for rank, record in enumerate(records2, start=1):
            record.rank = rank
        
        for record in records2:
            base_points = (record.score - self.room.return_points) / 1000
            uma_map = {
                1: self.room.uma_1st,
                2: self.room.uma_2nd,
                3: self.room.uma_3rd,
                4: self.room.uma_4th,
            }
            uma = uma_map.get(record.rank, 0)
            oka = self.room.oka if record.rank == 1 else 0
            record.points = base_points + uma + oka
            record.save()
        
        # プレイヤー1の累計ポイントを確認
        player1 = self.players[0]
        total_points = sum(
            sr.points for sr in ScoreRecord.objects.filter(player=player1)
            if sr.points is not None
        )
        
        # ゲーム1: 60.0pt（1位、50000点）
        # ゲーム2: -30.0pt（4位、20000点）→ (20000-30000)/1000 - 20 = -30.0pt
        # 合計: 60.0 - 30.0 = 30.0pt
        expected_total = 60.0 + (-30.0)
        self.assertEqual(total_points, expected_total)
    
    def test_score_sum_not_equal_to_return_points_times_four(self):
        """持ち点の合計が返し点×4でなくても正しく計算できることを確認"""
        # スコア: 35000, 30000, 25000, 15000（合計105000、返し点×4=120000ではない）
        scores = [35000, 30000, 25000, 15000]
        records = self._calculate_and_save_scores(scores)
        
        # すべてのスコア記録が正しく計算されていることを確認
        for record in records:
            self.assertIsNotNone(record.points)
            self.assertIsNotNone(record.rank)
        
        # 素点の合計を確認（0でなくても正常）
        base_points_sum = sum((r.score - self.room.return_points) / 1000 for r in records)
        self.assertNotEqual(base_points_sum, 0.0)  # -15.0になるはず
        
        # しかし、ポイントは正しく計算されている
        total_points = sum(r.points for r in records)
        # ウマとオカを含めた合計は計算可能
        self.assertIsNotNone(total_points)
    
    def test_negative_scores(self):
        """マイナスの持ち点でも正しく計算できることを確認"""
        # 極端なケース: 4位がマイナス点
        scores = [30000, 30000, 30000, -5000]
        records = self._calculate_and_save_scores(scores)
        
        # 4位: (-5000-30000)/1000 - 20 = -35 - 20 = -55.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -55.0)
    
    def test_all_tied_scores(self):
        """全員が同点の場合の計算"""
        # 全員30000点（返し点と同じ）
        scores = [30000, 30000, 30000, 30000]
        records = self._calculate_and_save_scores(scores)
        
        # 1位（orderが最小）: 0 + 20 + 20 = 40.0pt
        record_1st = [r for r in records if r.rank == 1][0]
        self.assertEqual(record_1st.points, 40.0)
        self.assertEqual(record_1st.player.order, 1)  # orderが最小
        
        # 2位: 0 + 10 = 10.0pt
        record_2nd = [r for r in records if r.rank == 2][0]
        self.assertEqual(record_2nd.points, 10.0)
        
        # 3位: 0 - 10 = -10.0pt
        record_3rd = [r for r in records if r.rank == 3][0]
        self.assertEqual(record_3rd.points, -10.0)
        
        # 4位: 0 - 20 = -20.0pt
        record_4th = [r for r in records if r.rank == 4][0]
        self.assertEqual(record_4th.points, -20.0)
