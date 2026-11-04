from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from lots.models import ItemLot, Category, Location
from .models import Notification

DISTRICTS = [
    'р. Исмоили Сомони',
    'р. Сино',
    'р. Фирдавси',
    'р. Шохмансур',
    'Центральный',
    'Советский',
    'Ленинский',
    'Октябрьский',
    'Приморский',
]

def lot_list_view(request):
    now = timezone.now()

    ItemLot.objects.filter(
        status='available',
        expiry_time__lte=now,
        category__lot_type='food',
        suitable_for_zoo=True,
        available_quantity__gt=0
    ).update(status='to_zoo')

    ItemLot.objects.filter(
        status='available',
        expiry_time__lte=now
    ).update(status='expired')

    lots = ItemLot.objects.filter(
        is_active=True,
        status='available',
        available_quantity__gt=0,
        expiry_time__gt=now
    ).select_related('category', 'location', 'donor')

    q = request.GET.get('q', '').strip()
    if q:
        lots = lots.filter(Q(title__icontains=q) | Q(description__icontains=q))

    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        lots = lots.filter(category__slug=category_slug)

    lot_type = request.GET.get('lot_type', '').strip()
    if lot_type in ['food', 'items']:
        lots = lots.filter(category__lot_type=lot_type)

    district = request.GET.get('district', '').strip()
    if district:
        lots = lots.filter(location__district=district)

    sort = request.GET.get('sort', '')
    if sort == 'new':
        lots = lots.order_by('-created_at')
    elif sort == 'weight':
        lots = lots.order_by('-weight_kg')
    else:
        lots = lots.order_by('expiry_time')

    categories = Category.objects.all()

    return render(request, 'core/lot_list.html', {
        'lots': lots,
        'categories': categories,
        'districts': DISTRICTS,
        'q': q,
        'selected_category': category_slug,
        'selected_lot_type': lot_type,
        'selected_district': district,
        'selected_sort': sort,
    })

@login_required
def mark_all_notifications_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('lot_list')

@login_required
def notification_click_view(request, pk):
    notif = get_object_or_404(request.user.notifications, pk=pk)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('user_cabinet')
