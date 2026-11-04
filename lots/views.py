from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.urls import reverse
from core.models import Notification
from .models import ItemLot, Category, Location, HelpRequest

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

def lot_detail_view(request, pk):
    now = timezone.now()
    lot = get_object_or_404(ItemLot.objects.select_related('category', 'location', 'donor', 'donor__profile'), pk=pk)
    if lot.status == 'available' and lot.expiry_time <= now:
        if lot.is_food and lot.suitable_for_zoo and lot.available_quantity > 0:
            lot.status = 'to_zoo'
        else:
            lot.status = 'expired'
        lot.save()
    return render(request, 'lots/lot_detail.html', {'lot': lot, 'now': now})

@login_required
def lot_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        district = request.POST.get('district', '').strip()
        address = request.POST.get('address', '').strip()
        pickup_instructions = request.POST.get('pickup_instructions', '').strip()
        quantity = request.POST.get('quantity')
        weight_kg = request.POST.get('weight_kg')
        expiry_time_raw = request.POST.get('expiry_time')
        image = request.FILES.get('image')
        suitable_for_zoo = 'suitable_for_zoo' in request.POST
        zoo_notes = request.POST.get('zoo_notes', '').strip()

        if not title or not description or not category_id or not district or not address or not quantity or not expiry_time_raw:
            messages.error(request, "Заполните все обязательные поля (включая район и адрес)!")
        else:
            try:
                category = Category.objects.get(pk=category_id)
                qty = int(quantity)
                if qty <= 0:
                    messages.error(request, "Количество должно быть больше 0!")
                    return redirect('lot_create')

                weight_val = float(str(weight_kg).replace(',', '.').strip())
                if weight_val <= 0 or weight_val > 9999.99:
                    messages.error(request, "Вес должен быть от 0.01 до 9999.99 кг!")
                    return redirect('lot_create')
                weight = round(weight_val, 2)

                location, _ = Location.objects.get_or_create(
                    district=district,
                    address=address,
                    defaults={
                        'title': f"Точка выдачи ({address})",
                        'pickup_instructions': pickup_instructions
                    }
                )
                dt = parse_datetime(expiry_time_raw)
                if dt and timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)

                lot = ItemLot.objects.create(
                    donor=request.user,
                    title=title,
                    description=description,
                    category=category,
                    location=location,
                    quantity=qty,
                    available_quantity=qty,
                    weight_kg=weight,
                    expiry_time=dt,
                    image=image,
                    suitable_for_zoo=suitable_for_zoo,
                    zoo_notes=zoo_notes,
                    status='available',
                    is_active=True
                )
                messages.success(request, f"Лот «{lot.title}» успешно опубликован!")
                return redirect('lot_detail', pk=lot.pk)
            except Exception as e:
                messages.error(request, f"Ошибка при создании: {e}")

    categories = Category.objects.all()
    return render(request, 'lots/lot_create.html', {'categories': categories, 'districts': DISTRICTS})

@login_required
def lot_edit_view(request, pk):
    lot = get_object_or_404(ItemLot, pk=pk)
    if lot.donor != request.user and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав на редактирование этого лота.")
    if request.method == 'POST':
        lot.title = request.POST.get('title', lot.title).strip()
        lot.description = request.POST.get('description', lot.description).strip()
        try:
            w_val = float(str(request.POST.get('weight_kg', lot.weight_kg)).replace(',', '.').strip())
            if 0 < w_val <= 9999.99:
                lot.weight_kg = round(w_val, 2)
        except (ValueError, TypeError):
            pass
        lot.suitable_for_zoo = 'suitable_for_zoo' in request.POST
        lot.zoo_notes = request.POST.get('zoo_notes', '').strip()
        if 'image' in request.FILES:
            lot.image = request.FILES['image']
        lot.save()
        messages.success(request, "Лот успешно обновлен!")
        return redirect('lot_detail', pk=lot.pk)
    return render(request, 'lots/lot_edit.html', {'lot': lot})

@login_required
def zoo_dashboard_view(request):
    if not (request.user.is_staff or request.user.profile.is_zoo_staff):
        return HttpResponseForbidden("Доступ разрешен только представителям зоопарка.")
    incoming_lots = ItemLot.objects.filter(
        status='to_zoo'
    ).select_related('category', 'location', 'donor', 'donor__profile').order_by('-expiry_time')
    return render(request, 'lots/zoo_dashboard.html', {'incoming_lots': incoming_lots})

@login_required
def zoo_accept_lot_view(request, pk):
    if not (request.user.is_staff or request.user.profile.is_zoo_staff):
        return HttpResponseForbidden("Доступ разрешен только представителям зоопарка.")
    lot = get_object_or_404(ItemLot, pk=pk, status='to_zoo')
    lot.status = 'zoo_received'
    lot.save()
    messages.success(request, f"Лот «{lot.title}» ({lot.weight_kg} кг) принят на баланс зоопарка!")
    return redirect('zoo_dashboard')

def help_request_list_view(request):
    help_requests = HelpRequest.objects.select_related('author', 'author__profile', 'helper', 'category').all()

    selected_status = request.GET.get('status', 'open')
    if selected_status and selected_status != 'all':
        help_requests = help_requests.filter(status=selected_status)

    selected_district = request.GET.get('district', '').strip()
    if selected_district:
        help_requests = help_requests.filter(district=selected_district)

    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        help_requests = help_requests.filter(category_id=selected_category)

    query = request.GET.get('q', '').strip()
    if query:
        help_requests = help_requests.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    categories = Category.objects.all()

    return render(request, 'lots/help_list.html', {
        'help_requests': help_requests,
        'categories': categories,
        'districts': DISTRICTS,
        'selected_district': selected_district,
        'selected_category': selected_category,
        'selected_status': selected_status,
        'query': query,
    })

@login_required
def help_request_create_view(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        district = request.POST.get('district', '').strip()
        urgency = request.POST.get('urgency', 'normal')
        contact_phone = request.POST.get('contact_phone', '').strip()

        if not title or not description or not category_id or not district:
            messages.error(request, "Заполните все обязательные поля (название, описание, категорию и район)!")
        else:
            category = get_object_or_404(Category, pk=category_id)
            if not contact_phone:
                contact_phone = request.user.profile.phone

            HelpRequest.objects.create(
                author=request.user,
                title=title,
                description=description,
                category=category,
                district=district,
                urgency=urgency,
                contact_phone=contact_phone,
            )
            messages.success(request, "Ваша просьба о помощи опубликована! Волонтеры и доноры увидят её.")
            return redirect('help_request_list')

    return render(request, 'lots/help_create.html', {
        'categories': categories,
        'districts': DISTRICTS,
    })

@login_required
def help_request_respond_view(request, pk):
    help_req = get_object_or_404(HelpRequest, pk=pk, status='open')

    if help_req.author == request.user:
        messages.error(request, "Вы не можете откликнуться на собственную заявку.")
        return redirect('help_request_list')

    help_req.status = 'in_progress'
    help_req.helper = request.user
    help_req.save()

    helper_phone = ''
    if request.user.profile.phone:
        helper_phone = f" (тел: {request.user.profile.phone})"

    Notification.objects.create(
        user=help_req.author,
        title="Волонтер готов помочь! ❤️",
        message=f"Пользователь {request.user.username} откликнулся на вашу просьбу «{help_req.title}»{helper_phone}.",
        link=reverse('help_request_list')
    )

    messages.success(request, f"Спасибо за ваше доброе сердце! Вы откликнулись на просьбу «{help_req.title}». Автор получил уведомление.")
    return redirect('help_request_list')

@login_required
def help_request_close_view(request, pk):
    help_req = get_object_or_404(HelpRequest, pk=pk)

    if help_req.author != request.user and help_req.helper != request.user and not request.user.is_staff:
        messages.error(request, "Только автор заявки или откликнувшийся волонтер может закрыть этот запрос.")
        return redirect('help_request_list')

    help_req.status = 'closed'
    help_req.save()
    messages.success(request, f"Запрос «{help_req.title}» отмечен как выполненный! Спасибо всем неравнодушным.")
    return redirect('help_request_list')
