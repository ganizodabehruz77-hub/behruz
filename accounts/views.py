from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from core.models import Notification
from lots.models import ItemLot
from .models import Profile, PartnerReview


def register(request):
    if request.user.is_authenticated:
        return redirect('lot_list')

    if request.method == 'POST':
        data = request.POST
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        p1 = data.get('password1', '')
        p2 = data.get('password2', '')
        phone = data.get('phone', '').strip()
        is_business = 'is_business' in data

        if not username or not email or not p1 or not p2:
            return render(request, 'accounts/register.html', {'error': 'Заполните все обязательные поля!'})
        if p1 != p2:
            return render(request, 'accounts/register.html', {'error': 'Пароли не совпадают!'})
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {'error': 'Пользователь с таким именем уже существует!'})
        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/register.html', {'error': 'Этот email уже используется!'})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=p1,
            is_active=False
        )

        Profile.objects.create(
            user=user,
            phone=phone,
            is_business=is_business
        )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = request.build_absolute_uri(
            reverse('activate', kwargs={'uidb64': uid, 'token': token})
        )

        try:
            send_mail(
                subject='Подтверждение регистрации | Делись Теплом',
                message=f'Здравствуйте, {user.username}!\n\nДля активации аккаунта перейдите по ссылке:\n{url}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )
        except Exception as e:
            user.delete()
            return render(request, 'accounts/register.html', {'error': f'Не удалось отправить письмо: {e}'})

        return render(request, 'accounts/email_sent.html', {'email': email})

    return render(request, 'accounts/register.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception as e:
        print(e)
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')

    return HttpResponse('<h1>Ссылка активации недействительна или устарела</h1>')


def login_user(request):
    if request.user.is_authenticated:
        return redirect('lot_list')

    if request.method == 'POST':
        data = request.POST
        username = data.get('username', '').strip()
        password = data.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('lot_list')
        return render(request, 'accounts/login.html', {'error': 'Неверный логин или пароль, либо аккаунт не активирован'})

    return render(request, 'accounts/login.html')


def logout_user(request):
    logout(request)
    return redirect('lot_list')


def partner_list_view(request):
    partners_qs = User.objects.filter(profile__is_business=True).select_related('profile')
    partners_data = []

    for p in partners_qs:
        revs = p.received_reviews.all()
        avg_r = round(sum(r.rating for r in revs) / len(revs), 1) if revs else 5.0
        donated_count = p.lots.filter(status__in=['completed', 'zoo_received']).count()
        active_count = p.lots.filter(status='available', is_active=True).count()
        partners_data.append({
            'partner': p,
            'reviews_count': len(revs),
            'avg_rating': avg_r,
            'donated_count': donated_count,
            'active_count': active_count,
        })

    return render(request, 'accounts/partner_list.html', {
        'partners_data': partners_data,
    })


def partner_detail_view(request, username):
    partner = get_object_or_404(User.objects.select_related('profile'), username=username, profile__is_business=True)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user == partner:
            messages.error(request, "Вы не можете оставить отзыв на собственное заведение.")
            return redirect('partner_detail', username=username)

        try:
            rating = int(request.POST.get('rating', 5))
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 5

        comment = request.POST.get('comment', '').strip()
        if comment:
            PartnerReview.objects.create(
                partner=partner,
                author=request.user,
                rating=rating,
                comment=comment,
            )
            Notification.objects.create(
                user=partner,
                title="Новый отзыв от жителя! ⭐",
                message=f"{request.user.username} оставил отзыв с оценкой {rating}★: «{comment[:50]}»",
                link=reverse('partner_detail', kwargs={'username': username})
            )
            messages.success(request, "Спасибо! Ваш теплый отзыв опубликован на странице заведения.")
            return redirect('partner_detail', username=username)
        else:
            messages.error(request, "Пожалуйста, напишите текст отзыва.")

    reviews = partner.received_reviews.select_related('author', 'author__profile').all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 5.0
    active_lots = ItemLot.objects.filter(donor=partner, status='available', is_active=True).select_related('category', 'location')
    total_saved_lots = partner.lots.filter(status__in=['completed', 'zoo_received']).count()

    return render(request, 'accounts/partner_detail.html', {
        'partner': partner,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'active_lots': active_lots,
        'total_saved_lots': total_saved_lots,
    })
