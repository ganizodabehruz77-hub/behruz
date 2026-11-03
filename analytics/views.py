from django.shortcuts import render
from django.db.models import Sum, Count
from lots.models import ItemLot
from reservations.models import Reservation

def impact_stats_view(request):
    food_people = ItemLot.objects.filter(
        category__lot_type='food',
        reservations__status='completed'
    ).distinct().aggregate(total=Sum('weight_kg'))['total'] or 0

    food_zoo = ItemLot.objects.filter(
        status='zoo_received'
    ).aggregate(total=Sum('weight_kg'))['total'] or 0

    items_count = Reservation.objects.filter(
        status='completed',
        lot__category__lot_type='items'
    ).aggregate(total=Sum('reserved_units'))['total'] or 0

    total_food_weight = float(food_people) + float(food_zoo)
    co2_saved = round(total_food_weight * 2.5, 2)

    top_districts = list(ItemLot.objects.filter(
        status__in=['completed', 'zoo_received']
    ).values('location__district').annotate(
        total_weight=Sum('weight_kg'),
        lots_count=Count('id')
    ).order_by('-total_weight')[:5])

    best_district = top_districts[0] if top_districts else None

    return render(request, 'analytics/impact_stats.html', {
        'food_people': food_people,
        'food_zoo': food_zoo,
        'items_count': items_count,
        'co2_saved': co2_saved,
        'top_districts': top_districts,
        'best_district': best_district,
    })
