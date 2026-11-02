from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from lots.models import ItemLot
from .models import Reservation, generate_pin_code

@login_required
def lot_reserve_view(request, pk):
    if request.method != 'POST':
        return redirect('lot_detail', pk=pk)

    now = timezone.now()

    with transaction.atomic():
        try:
            lot = ItemLot.objects.select_for_update().get(pk=pk)
        except ItemLot.DoesNotExist:
            messages.error(request, "Лот не найден.")
            return redirect('lot_list')

        if lot.donor == request.user:
            messages.error(request, "Вы не можете забрать собственный лот.")
            return redirect('lot_detail', pk=pk)

        if lot.expiry_time <= now or lot.status != 'available':
            messages.error(request, "Срок действия лота истек или он более недоступен.")
            return redirect('lot_detail', pk=pk)
        try:
            requested_count = int(request.POST.get('units', 1))
        except (ValueError, TypeError):
            requested_count = 1
        if requested_count <= 0:
            messages.error(request, "Укажите корректное количество единиц.")
            return redirect('lot_detail', pk=pk)
        if requested_count > lot.available_quantity:
            messages.error(request, f"Недостаточно доступных единиц. В наличии всего {lot.available_quantity} шт.")
            return redirect('lot_detail', pk=pk)
        lot.available_quantity -= requested_count
        if lot.available_quantity == 0:
            lot.status = 'reserved'
        lot.save()
        pin = generate_pin_code()
        reservation = Reservation.objects.create(
            user=request.user,
            lot=lot,
            reserved_units=requested_count,
            status='active',
            pin_code=pin
        )
        messages.success(request, f"Успешно забронировано {requested_count} шт.! Ваш PIN-код для получения: {pin}")
        return redirect('user_cabinet')

@login_required
def reservation_cancel_view(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user, status='active')
    with transaction.atomic():
        lot = ItemLot.objects.select_for_update().get(pk=reservation.lot.pk)
        lot.available_quantity += reservation.reserved_units
        if lot.status == 'reserved':
            lot.status = 'available'
        lot.save()
        reservation.status = 'cancelled'
        reservation.save()
    messages.info(request, "Бронирование отменено. Количество возвращено в доступные лоты.")
    return redirect('user_cabinet')

@login_required
def reservation_confirm_view(request, pk):
    if request.method == 'POST':
        pin = request.POST.get('pin_code', '').strip()
        reservation = get_object_or_404(
            Reservation.objects.select_related('lot'),
            pk=pk,
            status='active'
        )

        if reservation.lot.donor != request.user and not request.user.is_staff:
            messages.error(request, "Вы не являетесь автором этого лота.")
            return redirect('user_cabinet')

        if reservation.pin_code == pin:
            reservation.status = 'completed'
            reservation.save()

            if reservation.lot.available_quantity == 0:
                reservation.lot.status = 'completed'
                reservation.lot.save()

            messages.success(request, "Выдача успешно подтверждена! Лот передан.")
        else:
            messages.error(request, "Неверный PIN-код! Проверьте код у получателя.")

    return redirect('user_cabinet')

@login_required
def user_cabinet_view(request):
    my_lots = ItemLot.objects.filter(donor=request.user).select_related('category', 'location').order_by('-created_at')

    active_incoming_reservations = Reservation.objects.filter(
        lot__donor=request.user,
        status='active'
    ).select_related('lot', 'user')

    my_reservations = Reservation.objects.filter(user=request.user).select_related('lot', 'lot__location').order_by('-created_at')

    return render(request, 'reservations/user_cabinet.html', {
        'my_lots': my_lots,
        'active_incoming_reservations': active_incoming_reservations,
        'my_reservations': my_reservations,
    })
