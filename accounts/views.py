from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

from .models import Profile


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
