from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from core.models import Notification
from lots.models import ItemLot
from .models import Reservation, ReservationMessage, generate_pin_code

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

        if request.user.profile.is_business:
            messages.error(request, "Заведения и организации выступают только в роли доноров и не могут забирать продукты.")
            return redirect('lot_detail', pk=pk)

        if request.user.profile.rating_score < 30:
            messages.error(request, f"Ваш индекс надежности слишком низкий ({request.user.profile.rating_score}%). Вы временно не можете забирать лоты.")
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

        if lot.donor.email:
            send_mail(
                subject=f"Новая бронь: {lot.title} | Делись Теплом",
                message=(
                    f"Здравствуйте, {lot.donor.username}!\n\n"
                    f"Пользователь {request.user.username} забронировал ваш лот «{lot.title}» в количестве {requested_count} шт.\n\n"
                    f"Когда получатель придет, он покажет QR-код или назовет 4-значный PIN-код для подтверждения выдачи в личном кабинете.\n\n"
                    f"С уважением, сервис «Делись Теплом»"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[lot.donor.email],
                fail_silently=True
            )

        Notification.objects.create(
            user=lot.donor,
            title=f"Новая бронь: {lot.title}",
            message=f"Пользователь {request.user.username} забронировал {requested_count} шт.",
            link=reverse('user_cabinet')
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

        profile = request.user.profile
        profile.rating_score = max(0, profile.rating_score - 10)
        profile.save()

    messages.info(request, "Бронирование отменено. За отмену снято 10% индекса надежности.")
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

            receiver_profile = reservation.user.profile
            receiver_profile.rating_score = min(100, receiver_profile.rating_score + 2)
            receiver_profile.save()

            Notification.objects.create(
                user=reservation.user,
                title="Лот получен! 🎉",
                message=f"Донор {request.user.username} подтвердил выдачу «{reservation.lot.title}». Вам начислено +2% рейтинга!",
                link=reverse('user_cabinet')
            )

            messages.success(request, "Выдача успешно подтверждена! Лот передан.")
        else:
            messages.error(request, "Неверный PIN-код! Проверьте код у получателя.")

    return redirect('user_cabinet')

@login_required
def reservation_confirm_qr_view(request, pk, pin):
    reservation = get_object_or_404(
        Reservation.objects.select_related('lot'),
        pk=pk,
        status='active'
    )

    if reservation.lot.donor != request.user and not request.user.is_staff:
        messages.error(request, "Только автор этого лота может подтвердить выдачу по QR-коду.")
        return redirect('user_cabinet')

    if reservation.pin_code == pin:
        reservation.status = 'completed'
        reservation.save()

        if reservation.lot.available_quantity == 0:
            reservation.lot.status = 'completed'
            reservation.lot.save()

        receiver_profile = reservation.user.profile
        receiver_profile.rating_score = min(100, receiver_profile.rating_score + 2)
        receiver_profile.save()

        Notification.objects.create(
            user=reservation.user,
            title="Лот получен по QR-коду! 🎉",
            message=f"Донор {request.user.username} подтвердил передачу «{reservation.lot.title}». Вам начислено +2% рейтинга!",
            link=reverse('user_cabinet')
        )

        messages.success(request, f"Выдача успешно подтверждена по QR-коду! Лот «{reservation.lot.title}» передан.")
    else:
        messages.error(request, "Неверный или устаревший QR-код!")

    return redirect('user_cabinet')

@login_required
def user_cabinet_view(request):
    my_lots = ItemLot.objects.filter(donor=request.user).select_related('category', 'location').order_by('-created_at')

    active_incoming_reservations = Reservation.objects.filter(
        lot__donor=request.user,
        status='active'
    ).select_related('lot', 'user')

    my_reservations = Reservation.objects.filter(user=request.user).select_related('lot', 'lot__location').order_by('-created_at')

    my_given_food = ItemLot.objects.filter(
        donor=request.user,
        category__lot_type='food',
        status__in=['completed', 'zoo_received']
    ).aggregate(total=Sum('weight_kg'))['total'] or 0

    my_taken_food = ItemLot.objects.filter(
        reservations__user=request.user,
        reservations__status='completed',
        category__lot_type='food'
    ).distinct().aggregate(total=Sum('weight_kg'))['total'] or 0

    personal_food = round(float(my_given_food) + float(my_taken_food), 1)
    personal_co2 = round(personal_food * 2.5, 1)

    if personal_food >= 30:
        eco_rank = "Хранитель Планеты 🌳"
        eco_progress = 100
    elif personal_food >= 10:
        eco_rank = "Защитник Органики 🍃"
        eco_progress = int((personal_food / 30) * 100)
    elif personal_food > 0:
        eco_rank = "Друг Природы 🌿"
        eco_progress = int((personal_food / 10) * 100)
    else:
        eco_rank = "Эко-Новичок 🌱"
        eco_progress = 20

    return render(request, 'reservations/user_cabinet.html', {
        'my_lots': my_lots,
        'active_incoming_reservations': active_incoming_reservations,
        'my_reservations': my_reservations,
        'personal_food': personal_food,
        'personal_co2': personal_co2,
        'eco_rank': eco_rank,
        'eco_progress': eco_progress,
    })

@login_required
def reservation_chat_view(request, pk):
    reservation = get_object_or_404(
        Reservation.objects.select_related('lot', 'lot__donor', 'lot__location', 'user'),
        pk=pk
    )

    if request.user != reservation.user and request.user != reservation.lot.donor and not request.user.is_staff:
        messages.error(request, "У вас нет доступа к этому чату.")
        return redirect('user_cabinet')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            ReservationMessage.objects.create(
                reservation=reservation,
                sender=request.user,
                text=text
            )
            other_user = reservation.lot.donor if request.user == reservation.user else reservation.user
            Notification.objects.create(
                user=other_user,
                title=f"Сообщение от {request.user.username}",
                message=f"{text[:50]}",
                link=reverse('reservation_chat', kwargs={'pk': pk})
            )
            return redirect('reservation_chat', pk=pk)

    chat_messages = reservation.messages.select_related('sender').all()
    other_user = reservation.lot.donor if request.user == reservation.user else reservation.user

    return render(request, 'reservations/chat.html', {
        'reservation': reservation,
        'chat_messages': chat_messages,
        'other_user': other_user,
    })
