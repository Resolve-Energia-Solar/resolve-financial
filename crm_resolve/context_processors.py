from main.models import Board


def boards(request):
    return {'lead_boards': Board.objects.filter(type='L'), 'task_boards': Board.objects.filter(type='T')}