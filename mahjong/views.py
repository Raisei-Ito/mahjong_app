from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from .models import Room, Player, Game, ScoreRecord


def index(request):
    """トップ画面"""
    return render(request, 'mahjong/index.html')


def create_room(request):
    """部屋を作成"""
    if request.method == 'POST':
        room = Room.objects.create()
        return redirect('mahjong:room_setup', room_code=room.code)
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
    
    if request.method == 'POST':
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
                    
                    # スコアとチップの範囲チェック
                    if score < 0 or score > 200000:
                        raise ValueError(f'{player.name}の持ち点が範囲外です（0-200000点）')
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
            
            # 順位を判定（持ち点の高い順）
            score_records.sort(key=lambda x: x.score, reverse=True)
            for rank, record in enumerate(score_records, start=1):
                record.rank = rank
            
            # ポイントを計算
            for record in score_records:
                # ウマを取得（サシウマから計算）
                uma_map = {
                    1: room.uma_1st,
                    2: room.uma_2nd,
                    3: room.uma_3rd,
                    4: room.uma_4th,
                }
                uma = uma_map.get(record.rank, 0)
                
                # オカ（1位のみ、レートから自動計算）
                oka = room.oka_points if record.rank == 1 else 0
                
                # ポイント計算: (持ち点 - 返し点) / 1000 + ウマ + オカ
                points = (record.score - room.return_points) / 1000 + uma + oka
                record.points = points
            
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
    room = get_object_or_404(Room, code=room_code)
    players = Player.objects.filter(room=room).order_by('order')
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
        player_stats.append({
            'player': player,
            'total_points': total_points,
            'total_chips': total_chips,
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


def game_list_partial(request, room_code):
    """HTMX用のゲームリスト部分テンプレート"""
    room = get_object_or_404(Room, code=room_code)
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
    
    if request.method == 'POST':
        try:
            # サシウマ設定（バリデーション付き）
            sashi_uma_1_2 = int(request.POST.get('sashi_uma_1_2', 5))
            sashi_uma_3_4 = int(request.POST.get('sashi_uma_3_4', 10))
            if sashi_uma_1_2 < 0 or sashi_uma_1_2 > 1000 or sashi_uma_3_4 < 0 or sashi_uma_3_4 > 1000:
                raise ValueError("サシウマの値が範囲外です")
            room.sashi_uma_1_2 = sashi_uma_1_2
            room.sashi_uma_3_4 = sashi_uma_3_4
            
            # レート設定（バリデーション付き）
            rate_type = request.POST.get('rate_type', 'ten5')
            valid_rate_types = [choice[0] for choice in Room.RATE_CHOICES]
            if rate_type not in valid_rate_types:
                raise ValueError("無効なレートタイプです")
            room.rate_type = rate_type
            
            if room.rate_type == 'custom':
                custom_return_points = int(request.POST.get('custom_return_points', 30000))
                if custom_return_points < 0 or custom_return_points > 1000000:
                    raise ValueError("返し点の値が範囲外です")
                room.custom_return_points = custom_return_points
            
            # 持ち点設定（バリデーション付き）
            starting_points = int(request.POST.get('starting_points', 25000))
            if starting_points < 0 or starting_points > 1000000:
                raise ValueError("持ち点の値が範囲外です")
            room.starting_points = starting_points
            
            room.save()
            messages.success(request, '設定を更新しました。')
        except (ValueError, TypeError) as e:
            messages.error(request, f'入力値が無効です: {str(e)}')
        
        return redirect('mahjong:room_dashboard', room_code=room_code)
    
    return render(request, 'mahjong/room_settings.html', {
        'room': room,
    })
