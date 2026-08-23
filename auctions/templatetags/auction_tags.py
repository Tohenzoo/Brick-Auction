from django import template
from auctions.models import Bid

register = template.Library()

@register.simple_tag
def user_bids_count(user):
    if user.is_authenticated:
        # Считаем количество уникальных лотов, на которые пользователь делал ставки
        return Bid.objects.filter(user=user).values('listing').distinct().count()
    return 0