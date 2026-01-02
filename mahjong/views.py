from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Room, Player, Game, ScoreRecord


def update_room_last_used(room):
    """部屋の最終使用時刻を更新"""
    try:
        if hasattr(room, 'last_used_at'):
            room.last_used_at = timezone.now()
            room.save(update_fields=['last_used_at'])
    except Exception:
        # マイグレーションが実行されていない場合など、エラーを無視
        pass


def index(request):
    """トップ画面"""
    return render(request, 'mahjong/index.html')


def create_room(request):
    """部屋を作成"""
    if request.method == 'POST':
        try:
            # 部屋を作成（codeは自動生成される）
            room = Room.objects.create()
            # room.codeが正しく生成されているか確認
            if not room.code:
                # コードが生成されていない場合は手動で生成
                from .models import generate_room_code
                room.code = generate_room_code()
                room.save()
            # リダイレクト先のURLを生成
            return redirect('mahjong:room_setup', room_code=room.code)
        except Exception as e:
            messages.error(request, f'部屋の作成に失敗しました: {str(e)}')
            return redirect('mahjong:index')
    return redirect('mahjong:index')


def join_room(request):
    """部屋コードで既存の部屋に入る"""
    if request.method == 'POST':
        room_code = request.POST.get('room_code', '').strip().upper()
        if room_code:
            try:
                room = Room.objects.get(code=room_code)
                # プレイヤーが登録されているか確認
                if Player.objects.filter(room=room).count() == 4:
                    return redirect('mahjong:room_dashboard', room_code=room_code)
                else:
                    return redirect('mahjong:room_setup', room_code=room_code)
            except Room.DoesNotExist:
                messages.error(request, f'部屋コード「{room_code}」が見つかりませんでした。')
        else:
            messages.error(request, '部屋コードを入力してください。')
    return redirect('mahjong:index')


def room_setup(request, room_code):
    """プレイヤー登録画面"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    
    if request.method == 'POST':
        with transaction.atomic():
            # 既存のプレイヤーを削除
            Player.objects.filter(room=room).delete()
            
            # 4名のプレイヤーを登録（バリデーション付き）
            player_names = []
            for i in range(1, 5):
                name = request.POST.get(f'player_{i}', '').strip()
                if name:
                    # 名前の長さと文字種をチェック
                    if len(name) > 50:
                        messages.error(request, f'プレイヤー{i}の名前が長すぎます（最大50文字）')
                        players = Player.objects.filter(room=room)
                        return render(request, 'mahjong/room_setup.html', {
                            'room': room,
                            'players': players,
                        })
                    player_names.append((name, i))
            
            if len(player_names) != 4:
                messages.error(request, '4名のプレイヤー名を入力してください。')
                players = Player.objects.filter(room=room)
                return render(request, 'mahjong/room_setup.html', {
                    'room': room,
                    'players': players,
                })
            
            # プレイヤーを登録
            for name, order in player_names:
                Player.objects.create(room=room, name=name, order=order)
        
        # プレイヤーが4人登録されたらダッシュボードへ
        # トランザクション外で確認（コミット後の状態を確認）
        if Player.objects.filter(room=room).count() == 4:
            return redirect('mahjong:room_dashboard', room_code=room_code)
    
    players = Player.objects.filter(room=room)
    return render(request, 'mahjong/room_setup.html', {
        'room': room,
        'players': players,
    })


def record_score(request, room_code):
    """スコア入力画面"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    players = Player.objects.filter(room=room).order_by('order')
    
    if request.method == 'POST':
        with transaction.atomic():
            # 次のゲーム番号を取得
            last_game = Game.objects.filter(room=room).order_by('-game_number').first()
            game_number = (last_game.game_number + 1) if last_game else 1
            
            # ゲームを作成
            game = Game.objects.create(room=room, game_number=game_number)
            
            # スコア記録を作成（バリデーション付き）
            score_records = []
            for player in players:
                try:
                    score = int(request.POST.get(f'score_{player.id}', 0))
                    chip_change = int(request.POST.get(f'chip_{player.id}', 0))
                    
                    # スコアとチップの範囲チェック（マイナスも許可）
                    if score < -200000 or score > 200000:
                        raise ValueError(f'{player.name}の持ち点が範囲外です（-200000〜200000点）')
                    if abs(chip_change) > 10000:
                        raise ValueError(f'{player.name}のチップ増減が範囲外です（-10000〜10000）')
                    
                    score_records.append(ScoreRecord(
                        game=game,
                        player=player,
                        score=score,
                        chip_change=chip_change,
                    ))
                except (ValueError, TypeError) as e:
                    messages.error(request, f'入力値が無効です: {str(e)}')
                    return redirect('mahjong:record_score', room_code=room_code)
            
            # 順位を判定（持ち点の高い順、同点の場合はプレイヤー順で決定）
            # 同点時のウマオカ折半なし：同点でも順位を分ける（プレイヤー順で決定）
            # ソート: 持ち点の高い順、同点の場合はプレイヤー順（orderが小さい方が上位）
            score_records.sort(key=lambda x: (x.score, -x.player.order), reverse=True)
            # 順位を1,2,3,4と割り当て（同点でも順位を分ける）
            for rank, record in enumerate(score_records, start=1):
                record.rank = rank
            
            # ポイントを計算
            # 【計算フロー】
            # 1. 素点計算：返し点30,000を基準に (持ち点 - 返し点) / 1000 で計算
            # 2. ウマ加算：順位に応じたウマを加算（10-20の場合：1位+20, 2位+10, 3位-10, 4位-20）
            # 3. オカ加算：1位のみ、トップ取りのオカ（20pt）を加算
            # 注意：素点の合計が0でなくても調整しない（持ち点の合計が返し点×4でないのは正常）
            
            for record in score_records:
                # 1. 素点計算：返し点30,000を基準に計算
                base_points = (record.score - room.return_points) / 1000
                
                # 2. ウマを取得（サシウマから計算）
                uma_map = {
                    1: room.uma_1st,
                    2: room.uma_2nd,
                    3: room.uma_3rd,
                    4: room.uma_4th,
                }
                uma = uma_map.get(record.rank, 0)
                
                # 3. オカ（1位のみ、トップ取りの固定値を使用）
                # room.oka_pointsは返し点と持ち点の差（5pt）を返すが、正しくはroom.oka（20pt）を使う
                oka = room.oka if record.rank == 1 else 0
                
                # 最終ポイント計算: 素点 + ウマ + オカ
                record.points = base_points + uma + oka
            
            # 保存
            for record in score_records:
                record.save()
        
        return redirect('mahjong:room_dashboard', room_code=room_code)
    
    return render(request, 'mahjong/record_score.html', {
        'room': room,
        'players': players,
    })


def room_dashboard(request, room_code):
    """ダッシュボード画面"""
    try:
        room = get_object_or_404(Room, code=room_code)
        update_room_last_used(room)
        players = Player.objects.filter(room=room).order_by('order')
        
        # プレイヤーが4人未満の場合はプレイヤー登録画面にリダイレクト
        if players.count() < 4:
            return redirect('mahjong:room_setup', room_code=room_code)
        
        games = Game.objects.filter(room=room).order_by('-game_number')
        
        # 各プレイヤーの累計ポイントとチップを計算
        player_stats = []
        for player in players:
            total_points = sum(
                sr.points for sr in ScoreRecord.objects.filter(player=player)
                if sr.points is not None
            )
            total_chips = sum(
                sr.chip_change for sr in ScoreRecord.objects.filter(player=player)
            )
            # チップを実際の支払いポイントに換算
            # chip_point_rateは100で割った値で保存されているので、計算時に100倍する
            chip_point_rate = getattr(room, 'chip_point_rate', 1.0) or 1.0
            chip_points = total_chips * chip_point_rate * 100
            # 合計（ポイントは100倍、チップも100倍した実際の支払いポイント）
            total_amount_pt = (total_points * 100) + chip_points
            player_stats.append({
                'player': player,
                'total_points': total_points,
                'total_chips': total_chips,
                'chip_points': chip_points,
                'total_amount_pt': total_amount_pt,
            })
        
        # 各ゲームのスコア記録をプレイヤー順に整理（初期表示用）
        games_data = []
        for game in games:
            game_records = {}
            for record in game.score_records.all():
                game_records[record.player.id] = record
            games_data.append({
                'game': game,
                'records': [game_records.get(player.id) for player in players]
            })
        
        return render(request, 'mahjong/dashboard.html', {
            'room': room,
            'players': players,
            'games': games,
            'games_data': games_data,
            'player_stats': player_stats,
        })
    except Exception as e:
        # エラーが発生した場合はログに記録して、エラーページにリダイレクト
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'room_dashboard error: {str(e)}', exc_info=True)
        messages.error(request, f'ダッシュボードの読み込みに失敗しました: {str(e)}')
        return redirect('mahjong:index')


@csrf_exempt
@require_http_methods(["GET"])
def game_list_partial(request, room_code):
    """HTMX用のゲームリスト部分テンプレート"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    players = Player.objects.filter(room=room).order_by('order')
    games = Game.objects.filter(room=room).order_by('-game_number')
    
    # 各ゲームのスコア記録をプレイヤー順に整理
    games_data = []
    for game in games:
        game_records = {}
        for record in game.score_records.all():
            game_records[record.player.id] = record
        games_data.append({
            'game': game,
            'records': [game_records.get(player.id) for player in players]
        })
    
    return render(request, 'mahjong/partials/game_list.html', {
        'room': room,
        'players': players,
        'games_data': games_data,
    })


@csrf_exempt
@require_http_methods(["GET"])
def player_stats_partial(request, room_code):
    """HTMX用のプレイヤー統計部分テンプレート"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    players = Player.objects.filter(room=room).order_by('order')
    
    # 各プレイヤーの累計ポイントとチップを計算
    player_stats = []
    for player in players:
        total_points = sum(
            sr.points for sr in ScoreRecord.objects.filter(player=player)
            if sr.points is not None
        )
        total_chips = sum(
            sr.chip_change for sr in ScoreRecord.objects.filter(player=player)
        )
        # チップを実際の支払いポイントに換算
        chip_points = total_chips * room.chip_point_rate * 100
        # 合計（ポイントは100倍、チップも100倍した実際の支払いポイント）
        total_amount_pt = (total_points * 100) + chip_points
        player_stats.append({
            'player': player,
            'total_points': total_points,
            'total_chips': total_chips,
            'chip_points': chip_points,
            'total_amount_pt': total_amount_pt,
        })
    
    return render(request, 'mahjong/partials/player_stats.html', {
        'room': room,
        'players': players,
        'player_stats': player_stats,
    })


def delete_game(request, room_code, game_id):
    """ゲーム記録を削除"""
    room = get_object_or_404(Room, code=room_code)
    game = get_object_or_404(Game, id=game_id, room=room)
    
    if request.method == 'POST':
        game.delete()
        messages.success(request, f'ゲーム #{game.game_number} を削除しました。')
        return redirect('mahjong:room_dashboard', room_code=room_code)
    
    return redirect('mahjong:room_dashboard', room_code=room_code)


def delete_room(request, room_code):
    """部屋を削除"""
    room = get_object_or_404(Room, code=room_code)
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, '部屋を削除しました。')
        return redirect('mahjong:index')
    
    return redirect('mahjong:room_dashboard', room_code=room_code)


def edit_players(request, room_code):
    """プレイヤー情報を編集"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    
    if request.method == 'POST':
        # 既存のプレイヤーを削除
        Player.objects.filter(room=room).delete()
        
        # 4名のプレイヤーを登録（バリデーション付き）
        player_names = []
        for i in range(1, 5):
            name = request.POST.get(f'player_{i}', '').strip()
            if name:
                # 名前の長さをチェック
                if len(name) > 50:
                    messages.error(request, f'プレイヤー{i}の名前が長すぎます（最大50文字）')
                    players = Player.objects.filter(room=room).order_by('order')
                    return render(request, 'mahjong/room_setup.html', {
                        'room': room,
                        'players': players,
                        'is_edit': True,
                    })
                player_names.append((name, i))
        
        if len(player_names) != 4:
            messages.error(request, '4名のプレイヤー名を入力してください。')
            players = Player.objects.filter(room=room).order_by('order')
            return render(request, 'mahjong/room_setup.html', {
                'room': room,
                'players': players,
                'is_edit': True,
            })
        
        # プレイヤーを登録
        for name, order in player_names:
            Player.objects.create(room=room, name=name, order=order)
        
        messages.success(request, 'プレイヤー情報を更新しました。')
        return redirect('mahjong:room_dashboard', room_code=room_code)
    
    players = Player.objects.filter(room=room).order_by('order')
    return render(request, 'mahjong/room_setup.html', {
        'room': room,
        'players': players,
        'is_edit': True,
    })


def room_settings(request, room_code):
    """部屋設定を変更"""
    room = get_object_or_404(Room, code=room_code)
    update_room_last_used(room)
    
    if request.method == 'POST':
        try:
            # サシウマ設定（バリデーション付き）
            sashi_uma_type = request.POST.get('sashi_uma_type', '5-10')
            valid_sashi_uma_types = [choice[0] for choice in Room.SASHI_UMA_CHOICES]
            if sashi_uma_type not in valid_sashi_uma_types:
                raise ValueError("無効なサシウマタイプです")
            room.sashi_uma_type = sashi_uma_type
            
            # カスタムの場合は個別の値を設定
            if sashi_uma_type == 'custom':
                sashi_uma_1_2 = int(request.POST.get('sashi_uma_1_2', 5))
                sashi_uma_3_4 = int(request.POST.get('sashi_uma_3_4', 10))
                if sashi_uma_1_2 < 0 or sashi_uma_1_2 > 1000 or sashi_uma_3_4 < 0 or sashi_uma_3_4 > 1000:
                    raise ValueError("サシウマの値が範囲外です")
                room.sashi_uma_1_2 = sashi_uma_1_2
                room.sashi_uma_3_4 = sashi_uma_3_4
            
            # レート設定（バリデーション付き、参考情報として保持）
            rate_type = request.POST.get('rate_type', 'ten5')
            valid_rate_types = [choice[0] for choice in Room.RATE_CHOICES]
            if rate_type not in valid_rate_types:
                raise ValueError("無効なレートタイプです")
            room.rate_type = rate_type
            
            # 持ち点設定（バリデーション付き）
            starting_points = int(request.POST.get('starting_points', 25000))
            if starting_points < 0 or starting_points > 1000000:
                raise ValueError("持ち点の値が範囲外です (0-1000000)")
            room.starting_points = starting_points
            
            # 返し点設定（バリデーション付き）
            return_points = int(request.POST.get('return_points', 30000))
            if return_points < 0 or return_points > 1000000:
                raise ValueError("返し点の値が範囲外です (0-1000000)")
            room.return_points = return_points
            
            # チップ換算率設定（バリデーション付き）
            # 入力値は100倍した値で受け取り、100で割って保存する
            # 例：入力画面で100と入力すると、データベースには1.0として保存される
            # 計算時はそのまま使用（chip_point_rate * チップ数 = 実際の支払いポイント）
            chip_point_rate_input = float(request.POST.get('chip_point_rate', 100.0))
            if chip_point_rate_input < 0 or chip_point_rate_input > 100000:
                raise ValueError("チップ換算率の値が範囲外です（0-100000pt）")
            # 入力値を100で割って保存（データベースには1.0として保存）
            room.chip_point_rate = chip_point_rate_input / 100.0
            
            room.save()
            messages.success(request, '設定を更新しました。')
        except (ValueError, TypeError) as e:
            messages.error(request, f'入力値が無効です: {str(e)}')
        
        return redirect('mahjong:room_dashboard', room_code=room_code)
    
    return render(request, 'mahjong/room_settings.html', {
        'room': room,
    })
