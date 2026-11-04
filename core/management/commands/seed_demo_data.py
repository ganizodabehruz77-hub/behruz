import os
from decimal import Decimal
from datetime import timedelta
import urllib.request
from PIL import Image, ImageDraw

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Profile, PartnerReview
from lots.models import Category, Location, ItemLot, HelpRequest
from reservations.models import Reservation, ReservationMessage
from core.models import Notification


class Command(BaseCommand):
    help = 'Populates database with rich demo data and photos'

    def handle(self, *args, **options):
        os.makedirs('media/lots', exist_ok=True)

        photo_seeds = {
            'bread.jpg': ('bakery77', (230, 160, 80)),
            'hot_food.jpg': ('dinner55', (210, 80, 50)),
            'apples.jpg': ('fruit99', (180, 50, 50)),
            'carrots.jpg': ('vegetables33', (230, 120, 30)),
            'jacket.jpg': ('fashion44', (60, 100, 180)),
            'dairy.jpg': ('milk22', (100, 180, 220)),
            'grocery.jpg': ('market11', (160, 140, 90)),
            'books.jpg': ('child88', (140, 70, 160)),
        }

        for fname, (seed, color) in photo_seeds.items():
            fpath = os.path.join('media/lots', fname)
            if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
                downloaded = False
                try:
                    url = f'https://picsum.photos/seed/{seed}/600/400'
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    content = urllib.request.urlopen(req, timeout=5).read()
                    if len(content) > 1000:
                        with open(fpath, 'wb') as f:
                            f.write(content)
                        downloaded = True
                except Exception:
                    downloaded = False

                if not downloaded:
                    img = Image.new('RGB', (600, 400), color)
                    d = ImageDraw.Draw(img)
                    d.rectangle([20, 20, 580, 380], outline=(255, 255, 255), width=6)
                    d.rectangle([50, 50, 550, 120], fill=(255, 255, 255))
                    img.save(fpath)

        categories_data = [
            ('Хлеб и выпечка', 'bread', 'food'),
            ('Горячие блюда', 'hot-food', 'food'),
            ('Фрукты и овощи', 'fruits-vegetables', 'food'),
            ('Бакалея и крупы', 'grocery', 'food'),
            ('Молочная продукция', 'dairy', 'food'),
            ('Одежда и обувь', 'clothes', 'items'),
            ('Детские товары', 'kids-items', 'items'),
        ]

        cat_map = {}
        for name, slug, lot_type in categories_data:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'lot_type': lot_type})
            cat_map[slug] = cat

        locations_data = [
            ('Пекарня на Рудаки', 'р. Исмоили Сомони', 'ул. Рудаки, 45', 'Центральный вход, спросить администратора Анну.', False),
            ('Чайхана Сомони', 'р. Сино', 'пр. Исмоили Сомони, 12', 'Боковой вход со двора, выдача с 14:00 до 20:00.', False),
            ('Эко-Маркет Баракат', 'р. Фирдавси', 'ул. Айни, 88', 'Зона погрузки со двора, звонок у белой двери.', False),
            ('Пункт добрососедства Сино', 'р. Сино', 'ул. Маяковского, 14', 'Подъезд 3, домофон 45.', False),
            ('Городской Зоопарк (ЗооШеринг)', 'р. Исмоили Сомони', 'пр. Рудаки, 180', 'Служебный въезд зоопарка, ветеринарный пункт приёма кормов.', True),
        ]

        loc_map = {}
        for title, district, addr, instr, is_zoo in locations_data:
            loc, _ = Location.objects.get_or_create(title=title, defaults={
                'district': district,
                'address': addr,
                'pickup_instructions': instr,
                'is_zoo': is_zoo
            })
            loc_map[title] = loc

        users_info = [
            ('baker_anna', 'anna@example.com', '+7 999 111-22-33', True, False, 'Пекарня «Хлебный Дар»', 'Каждое утро выпекаем свежий хлеб и выпечку. Всю нераспроданную свежую продукцию передаем семьям и приютам города.', 'ул. Рудаки, 45'),
            ('cafe_dushanbe', 'cafe@example.com', '+7 999 222-33-44', True, False, 'Кафе «Чайхана & Выпечка»', 'Традиционные горячие блюда, самса и плов. Мы за Zero Waste — спасаем вкусную качественную еду!', 'пр. Исмоили Сомони, 12'),
            ('market_barakat', 'market@example.com', '+7 999 333-44-55', True, False, 'Эко-Маркет «Баракат»', 'Фрукты, овощи и крупы. Делимся излишками с жителями и зоопарком города.', 'ул. Айни, 88'),
            ('zoo_staff_petr', 'zoo@example.com', '+7 999 444-55-66', False, True, '', '', ''),
            ('maria_eco', 'maria@example.com', '+7 999 555-66-77', False, False, '', '', ''),
            ('rustam_volunteer', 'rustam@example.com', '+7 999 666-77-88', False, False, '', '', ''),
            ('lenovo', 'lenovo@example.com', '+7 999 000-00-01', False, False, '', '', ''),
        ]

        user_map = {}
        for username, email, phone, is_biz, is_zoo, comp, bio, addr in users_info:
            u = User.objects.filter(username=username).first()
            if not u:
                u = User.objects.create_user(username=username, email=email, password='password123', is_active=True)
            p, _ = Profile.objects.get_or_create(user=u)
            p.phone = phone
            p.is_business = is_biz
            p.is_zoo_staff = is_zoo
            p.company_name = comp
            p.bio = bio
            p.address = addr
            p.save()
            user_map[username] = u

        now = timezone.now()

        lots_data = [
            {
                'donor': user_map['baker_anna'],
                'title': 'Свежие французские багеты и круассаны',
                'description': 'Хрустящая утренняя выпечка без консервантов. Упакована в крафтовые пакеты по 3 шт. Отлично к чаю для семьи.',
                'category': cat_map['bread'],
                'location': loc_map['Пекарня на Рудаки'],
                'quantity': 15,
                'available_quantity': 12,
                'weight_kg': Decimal('4.50'),
                'expiry_time': now + timedelta(days=2),
                'image': 'lots/bread.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
            {
                'donor': user_map['cafe_dushanbe'],
                'title': 'Традиционный таджикский плов (ланч-боксы)',
                'description': 'Горячий свежий плов с говядиной и нутом, упакован в герметичные термобоксы. Приготовлен сегодня в 12:00.',
                'category': cat_map['hot-food'],
                'location': loc_map['Чайхана Сомони'],
                'quantity': 10,
                'available_quantity': 7,
                'weight_kg': Decimal('5.00'),
                'expiry_time': now + timedelta(hours=14),
                'image': 'lots/hot_food.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
            {
                'donor': user_map['market_barakat'],
                'title': 'Спелые яблоки и груши (сочные)',
                'description': 'Яблоки сладкие красные и груши. Подходят как людям, так и животным в приют или зоопарк.',
                'category': cat_map['fruits-vegetables'],
                'location': loc_map['Эко-Маркет Баракат'],
                'quantity': 25,
                'available_quantity': 20,
                'weight_kg': Decimal('18.50'),
                'expiry_time': now + timedelta(days=3),
                'image': 'lots/apples.jpg',
                'suitable_for_zoo': True,
                'zoo_notes': 'Любимое лакомство для медведей, обезьян и птиц зоопарка.',
                'status': 'available',
            },
            {
                'donor': user_map['market_barakat'],
                'title': 'Свежая морковь и сладкая тыква',
                'description': 'Крупная мытая морковь и нарезанная тыква. Идеально для приготовления каш или витаминной подкормки животных.',
                'category': cat_map['fruits-vegetables'],
                'location': loc_map['Эко-Маркет Баракат'],
                'quantity': 30,
                'available_quantity': 28,
                'weight_kg': Decimal('25.00'),
                'expiry_time': now + timedelta(days=4),
                'image': 'lots/carrots.jpg',
                'suitable_for_zoo': True,
                'zoo_notes': 'Отличный рацион для копытных, слонов и кроликов.',
                'status': 'available',
            },
            {
                'donor': user_map['maria_eco'],
                'title': 'Зимний пуховик унисекс (рост 165-175 см)',
                'description': 'Очень тёплый синий пуховик с капюшоном в отличном состоянии. Все замки работают, чистый после химчистки.',
                'category': cat_map['clothes'],
                'location': loc_map['Пункт добрососедства Сино'],
                'quantity': 1,
                'available_quantity': 1,
                'weight_kg': Decimal('1.80'),
                'expiry_time': now + timedelta(days=30),
                'image': 'lots/jacket.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
            {
                'donor': user_map['baker_anna'],
                'title': 'Свежее фермерское молоко и творог 9%',
                'description': 'Натуральное пастеризованное молоко (3 бутылки по 1 л) и свежий рассыпчатый домашний творог.',
                'category': cat_map['dairy'],
                'location': loc_map['Пекарня на Рудаки'],
                'quantity': 6,
                'available_quantity': 5,
                'weight_kg': Decimal('4.20'),
                'expiry_time': now + timedelta(days=2),
                'image': 'lots/dairy.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
            {
                'donor': user_map['rustam_volunteer'],
                'title': 'Набор развивающих книг и настольных игр',
                'description': 'Энциклопедии для школьников, детские сказки и настольная игра-ходилка. Подойдет многодетной семье.',
                'category': cat_map['kids-items'],
                'location': loc_map['Пункт добрососедства Сино'],
                'quantity': 4,
                'available_quantity': 4,
                'weight_kg': Decimal('2.50'),
                'expiry_time': now + timedelta(days=45),
                'image': 'lots/books.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
            {
                'donor': user_map['market_barakat'],
                'title': 'Бакалейный набор: рис для плова и гречка',
                'description': 'Упаковки по 1 кг круглозерного риса и гречневой крупы высшего сорта. Срок годности с запасом.',
                'category': cat_map['grocery'],
                'location': loc_map['Эко-Маркет Баракат'],
                'quantity': 12,
                'available_quantity': 10,
                'weight_kg': Decimal('10.00'),
                'expiry_time': now + timedelta(days=60),
                'image': 'lots/grocery.jpg',
                'suitable_for_zoo': False,
                'zoo_notes': '',
                'status': 'available',
            },
        ]

        for lot_dict in lots_data:
            if not ItemLot.objects.filter(title=lot_dict['title']).exists():
                ItemLot.objects.create(**lot_dict)

        test_lot = ItemLot.objects.filter(title__icontains='багеты').first()
        if test_lot and not Reservation.objects.filter(lot=test_lot, user=user_map['lenovo'], status='active').exists():
            res = Reservation.objects.create(
                lot=test_lot,
                user=user_map['lenovo'],
                reserved_units=2,
                status='active',
                pin_code='7412'
            )
            ReservationMessage.objects.create(
                reservation=res,
                sender=user_map['lenovo'],
                text='Здравствуйте! Я забронировал багеты. Буду около 18:30, захвачу свой пакет.'
            )
            ReservationMessage.objects.create(
                reservation=res,
                sender=user_map['baker_anna'],
                text='Добрый день! Отлично, ваши багеты отложены. Подходите к кассе №1!'
            )

        help_requests_data = [
            {
                'author': user_map['maria_eco'],
                'helper': user_map['rustam_volunteer'],
                'title': 'Крупы и сухой корм для 12 кошек в приюте',
                'description': 'Очень нужны овсяные хлопья, гречневая сечка и любой корм для спасённых котят и кошек.',
                'category': cat_map['grocery'],
                'district': 'р. Сино',
                'urgency': 'high',
                'status': 'in_progress',
                'contact_phone': '+7 999 555-66-77',
            },
            {
                'author': user_map['rustam_volunteer'],
                'helper': None,
                'title': 'Теплые зимние сапоги для девочки (размер 33-34)',
                'description': 'Семья с радостью примет детские зимние сапоги или ботинки в хорошем состоянии.',
                'category': cat_map['clothes'],
                'district': 'р. Фирдавси',
                'urgency': 'normal',
                'status': 'open',
                'contact_phone': '+7 999 666-77-88',
            },
        ]

        for hd in help_requests_data:
            if not HelpRequest.objects.filter(title=hd['title']).exists():
                HelpRequest.objects.create(**hd)

        reviews_data = [
            (user_map['baker_anna'], user_map['maria_eco'], 5, 'Огромная благодарность пекарне за свежайшие круассаны! Дети в восторге ❤️'),
            (user_map['baker_anna'], user_map['rustam_volunteer'], 5, 'Всегда вежливый персонал и вкусный хрустящий хлеб. Прекрасное заведение!'),
            (user_map['cafe_dushanbe'], user_map['maria_eco'], 5, 'Спасибо за спасение еды! Очень вкусный плов, выручили волонтеров на смене.'),
            (user_map['market_barakat'], user_map['rustam_volunteer'], 5, 'Отличный эко-маркет! Регулярно передают свежие фрукты и овощи.'),
        ]

        for partner, author, rating, comment in reviews_data:
            if not PartnerReview.objects.filter(partner=partner, author=author).exists():
                PartnerReview.objects.create(partner=partner, author=author, rating=rating, comment=comment)

        if not Notification.objects.filter(user=user_map['lenovo'], title__icontains='Добро пожаловать').exists():
            Notification.objects.create(
                user=user_map['lenovo'],
                title='Добро пожаловать в «Делись Теплом»!',
                message='Платформа готова к работе. У вас есть активное бронирование с PIN-кодом и QR-кодом.',
                link='/reservations/my-cabinet/'
            )

        self.stdout.write(self.style.SUCCESS('Successfully loaded rich demo data with photos!'))
