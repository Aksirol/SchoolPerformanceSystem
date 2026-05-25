"""
Сід-файл для системи обліку успішності учнів школи.

Запуск:
    python manage.py shell < seed.py

Що створює:
    - 2 навчальні роки (2023-2024, 2024-2025) по 2 семестри
    - 14 предметів
    - 16 вчителів (з яких 6 — також класні керівники)
    - 6 класів (5-А, 7-Б, 9-А, 9-Б, 10-А, 11-А)
    - 138 учнів (20–25 на клас)
    - призначення вчителів на предмети в класах
    - ~2 400 оцінок з реалістичним розподілом
    - облікові записи для всіх акторів (admin / вчителі / учні)
"""

import random
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from school.models import (
    User, AcademicYear, Semester, Teacher, Subject,
    SchoolClass, Student, TeacherSubject, Grade,
)

random.seed(42)

# ---------------------------------------------------------------------------
# Допоміжні функції
# ---------------------------------------------------------------------------

def rnd_phone():
    operators = ['050', '067', '073', '095', '099', '063', '066', '093', '068']
    op = random.choice(operators)
    num = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return f'+380{op[1:]}{num}'


def rnd_birth_date(grade_number):
    """Генерує реалістичну дату народження для учня певного класу (2024-2025 рік)."""
    birth_year = 2024 - 6 - grade_number  # орієнтовний рік народження
    birth_year += random.randint(-1, 1)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(birth_year, month, day)


def rnd_grade_value(student_level):
    """
    Повертає реалістичну оцінку за 12-бальною шкалою.
    student_level: 'strong' | 'average' | 'weak'
    """
    if student_level == 'strong':
        return random.choices(range(1, 13), weights=[0,0,0,0,1,2,4,7,12,18,25,31])[0]
    elif student_level == 'average':
        return random.choices(range(1, 13), weights=[0,0,1,2,4,8,14,20,22,16,9,4])[0]
    else:  # weak
        return random.choices(range(1, 13), weights=[2,4,8,14,18,20,16,10,5,2,1,0])[0]


# ---------------------------------------------------------------------------
# Дані
# ---------------------------------------------------------------------------

FIRST_NAMES_MALE = [
    'Олександр', 'Максим', 'Дмитро', 'Андрій', 'Іван', 'Артем',
    'Богдан', 'Микола', 'Ярослав', 'Юрій', 'Євген', 'Тарас',
    'Владислав', 'Роман', 'Сергій', 'Василь', 'Павло', 'Денис',
    'Кирило', 'Антон', 'Олег', 'Ігор', 'Назар', 'Віктор', 'Данило',
]

FIRST_NAMES_FEMALE = [
    'Анна', 'Марія', 'Олена', 'Наталія', 'Тетяна', 'Ірина',
    'Вікторія', 'Юлія', 'Христина', 'Дарина', 'Катерина', 'Ольга',
    'Людмила', 'Надія', 'Аліна', 'Валентина', 'Лілія', 'Оксана',
    'Поліна', 'Діана', 'Аліса', 'Світлана', 'Галина', 'Уляна', 'Мирослава',
]

LAST_NAMES = [
    'Коваленко', 'Шевченко', 'Бойко', 'Ткаченко', 'Кравченко',
    'Мороз', 'Лисенко', 'Павленко', 'Олійник', 'Гончаренко',
    'Мельник', 'Коваль', 'Пономаренко', 'Середа', 'Науменко',
    'Хоменко', 'Дорошенко', 'Яременко', 'Марченко', 'Кириленко',
    'Сидоренко', 'Волошин', 'Захаренко', 'Вовк', 'Сергієнко',
    'Гриценко', 'Савченко', 'Остапенко', 'Луценко', 'Романенко',
    'Власенко', 'Харченко', 'Маценко', 'Пилипенко', 'Даниленко',
    'Ільченко', 'Бондаренко', 'Нечипоренко', 'Педченко', 'Мисник',
]

TEACHER_DATA = [
    # (Прізвище, Ім'я, email_prefix, телефон, головний предмет)
    ('Петренко',   'Світлана',   'petrovia_s',   '0671234001', 'Математика'),
    ('Іванченко',  'Василь',     'ivanchenko_v', '0501234002', 'Фізика'),
    ('Захарченко', 'Оксана',     'zakharch_o',   '0951234003', 'Хімія'),
    ('Кравченко',  'Микола',     'kravch_m',     '0631234004', 'Біологія'),
    ('Мороз',      'Тетяна',     'moroz_t',      '0671234005', 'Українська мова'),
    ('Савченко',   'Людмила',    'savchenko_l',  '0501234006', 'Українська мова'),
    ('Романенко',  'Ігор',       'romanenko_i',  '0731234007', 'Зарубіжна література'),
    ('Власенко',   'Наталія',    'vlasenko_n',   '0951234008', 'Англійська мова'),
    ('Луценко',    'Олена',      'lutsenko_o',   '0671234009', 'Англійська мова'),
    ('Гончаренко', 'Сергій',     'goncharenko_s','0501234010', 'Географія'),
    ('Яременко',   'Алла',       'yaremenko_a',  '0631234011', 'Історія'),
    ('Хоменко',    'Дмитро',     'khomenko_d',   '0731234012', 'Інформатика'),
    ('Науменко',   'Ірина',      'naumenko_i',   '0951234013', 'Фізична культура'),
    ('Дорошенко',  'Андрій',     'doroshenko_a', '0501234014', 'Математика'),
    ('Бойко',      'Галина',     'boyko_g',      '0671234015', 'Музичне мистецтво'),
    ('Лисенко',    'Павло',      'lysenko_p',    '0631234016', 'Образотворче мистецтво'),
]

SUBJECTS_DATA = [
    ('Математика',               'Алгебра, геометрія, початки аналізу'),
    ('Фізика',                   'Механіка, термодинаміка, електродинаміка, оптика'),
    ('Хімія',                    'Загальна, органічна та неорганічна хімія'),
    ('Біологія',                 'Анатомія, ботаніка, зоологія, генетика'),
    ('Українська мова',          'Граматика, орфографія, пунктуація, стилістика'),
    ('Українська література',    'Твори класичної та сучасної української літератури'),
    ('Зарубіжна література',     'Твори світової літератури у перекладі'),
    ('Англійська мова',          'Граматика, читання, письмо, аудіювання'),
    ('Географія',                'Фізична та соціально-економічна географія'),
    ('Історія України',          'Від давніх часів до сучасності'),
    ('Всесвітня історія',        'Від стародавнього світу до сучасності'),
    ('Інформатика',              'Алгоритми, програмування, офісні застосунки, безпека'),
    ('Фізична культура',         'Загальна фізична підготовка, спортивні ігри'),
    ('Музичне мистецтво',        'Теорія музики, слухання, вокал'),
]

CLASS_DEFINITIONS = [
    # (назва, клас_номер, кількість учнів, індекс класного_керівника у TEACHER_DATA)
    ('5-А',  5,  23, 4),   # кл. кер. — Мороз Тетяна
    ('7-Б',  7,  24, 5),   # кл. кер. — Савченко Людмила
    ('9-А',  9,  25, 0),   # кл. кер. — Петренко Світлана
    ('9-Б',  9,  24, 6),   # кл. кер. — Романенко Ігор
    ('10-А', 10, 22, 10),  # кл. кер. — Яременко Алла
    ('11-А', 11, 20, 7),   # кл. кер. — Власенко Наталія
]

# Предмети для кожного класу: (індекс предмету, індекс вчителя)
# Індекси відповідають спискам SUBJECTS_DATA та TEACHER_DATA
CLASS_SUBJECTS = {
    '5-А': [
        (0, 0),   # Математика      — Петренко С.
        (4, 4),   # Укр. мова       — Мороз Т.
        (5, 4),   # Укр. літ.       — Мороз Т.
        (6, 6),   # Зарубіжна літ.  — Романенко І.
        (7, 7),   # Англійська      — Власенко Н.
        (8, 9),   # Географія       — Гончаренко С.
        (9, 10),  # Історія         — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
        (13,14),  # Музика          — Бойко Г.
    ],
    '7-Б': [
        (0, 13),  # Математика      — Дорошенко А.
        (1, 1),   # Фізика          — Іванченко В.
        (2, 2),   # Хімія           — Захарченко О.
        (3, 3),   # Біологія        — Кравченко М.
        (4, 5),   # Укр. мова       — Савченко Л.
        (5, 5),   # Укр. літ.       — Савченко Л.
        (6, 6),   # Зарубіжна літ.  — Романенко І.
        (7, 8),   # Англійська      — Луценко О.
        (8, 9),   # Географія       — Гончаренко С.
        (9, 10),  # Історія         — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
    ],
    '9-А': [
        (0, 0),   # Математика      — Петренко С.
        (1, 1),   # Фізика          — Іванченко В.
        (2, 2),   # Хімія           — Захарченко О.
        (3, 3),   # Біологія        — Кравченко М.
        (4, 4),   # Укр. мова       — Мороз Т.
        (5, 4),   # Укр. літ.       — Мороз Т.
        (6, 6),   # Зарубіжна літ.  — Романенко І.
        (7, 7),   # Англійська      — Власенко Н.
        (8, 9),   # Географія       — Гончаренко С.
        (9, 10),  # Історія         — Яременко А.
        (10,10),  # Всесвітня іст.  — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
    ],
    '9-Б': [
        (0, 13),  # Математика      — Дорошенко А.
        (1, 1),   # Фізика          — Іванченко В.
        (2, 2),   # Хімія           — Захарченко О.
        (3, 3),   # Біологія        — Кравченко М.
        (4, 5),   # Укр. мова       — Савченко Л.
        (5, 5),   # Укр. літ.       — Савченко Л.
        (6, 6),   # Зарубіжна літ.  — Романенко І.
        (7, 8),   # Англійська      — Луценко О.
        (9, 10),  # Історія         — Яременко А.
        (10,10),  # Всесвітня іст.  — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
    ],
    '10-А': [
        (0, 0),   # Математика      — Петренко С.
        (1, 1),   # Фізика          — Іванченко В.
        (2, 2),   # Хімія           — Захарченко О.
        (3, 3),   # Біологія        — Кравченко М.
        (4, 4),   # Укр. мова       — Мороз Т.
        (5, 4),   # Укр. літ.       — Мороз Т.
        (7, 7),   # Англійська      — Власенко Н.
        (9, 10),  # Історія         — Яременко А.
        (10,10),  # Всесвітня іст.  — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
    ],
    '11-А': [
        (0, 13),  # Математика      — Дорошенко А.
        (1, 1),   # Фізика          — Іванченко В.
        (2, 2),   # Хімія           — Захарченко О.
        (3, 3),   # Біологія        — Кравченко М.
        (4, 5),   # Укр. мова       — Савченко Л.
        (5, 5),   # Укр. літ.       — Савченко Л.
        (7, 8),   # Англійська      — Луценко О.
        (9, 10),  # Історія         — Яременко А.
        (10,10),  # Всесвітня іст.  — Яременко А.
        (11,11),  # Інформатика     — Хоменко Д.
        (12,12),  # Фіз. культура   — Науменко І.
    ],
}

# ---------------------------------------------------------------------------
# Очищення бази
# ---------------------------------------------------------------------------

print('Очищення старих даних...')
Grade.objects.all().delete()
TeacherSubject.objects.all().delete()
Student.objects.all().delete()
SchoolClass.objects.all().delete()
Teacher.objects.all().delete()
Subject.objects.all().delete()
Semester.objects.all().delete()
AcademicYear.objects.all().delete()
User.objects.all().delete()

# ---------------------------------------------------------------------------
# Адміністратор
# ---------------------------------------------------------------------------

print('Створення адміністратора...')
admin = User.objects.create(
    username='admin',
    password=make_password('admin1234'),
    first_name='Директор',
    last_name='Школи',
    email='admin@school.edu.ua',
    role='admin',
    is_staff=True,
    is_superuser=True,
)

# ---------------------------------------------------------------------------
# Навчальні роки та семестри
# ---------------------------------------------------------------------------

print('Створення навчальних років...')
ay_2324 = AcademicYear.objects.create(
    name='2023-2024',
    start_date=date(2023, 9, 1),
    end_date=date(2024, 5, 31),
)
ay_2425 = AcademicYear.objects.create(
    name='2024-2025',
    start_date=date(2024, 9, 2),
    end_date=date(2025, 5, 30),
)

sem1_2324 = Semester.objects.create(number=1, academic_year=ay_2324,
                                     start_date=date(2023, 9, 1), end_date=date(2023, 12, 29))
sem2_2324 = Semester.objects.create(number=2, academic_year=ay_2324,
                                     start_date=date(2024, 1, 15), end_date=date(2024, 5, 31))
sem1_2425 = Semester.objects.create(number=1, academic_year=ay_2425,
                                     start_date=date(2024, 9, 2), end_date=date(2024, 12, 27))
sem2_2425 = Semester.objects.create(number=2, academic_year=ay_2425,
                                     start_date=date(2025, 1, 13), end_date=date(2025, 5, 30))

semesters_by_year = {
    ay_2324.id: [sem1_2324, sem2_2324],
    ay_2425.id: [sem1_2425, sem2_2425],
}

# ---------------------------------------------------------------------------
# Предмети
# ---------------------------------------------------------------------------

print('Створення предметів...')
subjects = []
for name, desc in SUBJECTS_DATA:
    subjects.append(Subject.objects.create(name=name, description=desc))

# ---------------------------------------------------------------------------
# Вчителі
# ---------------------------------------------------------------------------

print('Створення вчителів...')
teachers = []
used_lastnames = set()

for i, (last, first, email_prefix, phone, _) in enumerate(TEACHER_DATA):
    # Роль: класні керівники (ті, що є у CLASS_DEFINITIONS) — 'homeroom', решта — 'teacher'
    homeroom_indices = {cd[3] for cd in CLASS_DEFINITIONS}
    role = 'homeroom' if i in homeroom_indices else 'teacher'

    username = f't_{email_prefix}'
    user = User.objects.create(
        username=username,
        password=make_password('teacher1234'),
        first_name=first,
        last_name=last,
        email=f'{email_prefix}@school.edu.ua',
        role=role,
    )
    teacher = Teacher.objects.create(
        user=user,
        first_name=first,
        last_name=last,
        email=f'{email_prefix}@school.edu.ua',
        phone=phone,
    )
    teachers.append(teacher)

# ---------------------------------------------------------------------------
# Класи (для навчального року 2024-2025)
# ---------------------------------------------------------------------------

print('Створення класів...')
classes = {}
for class_name, grade_num, student_count, hr_teacher_idx in CLASS_DEFINITIONS:
    sc = SchoolClass.objects.create(
        name=class_name,
        grade_number=grade_num,
        academic_year=ay_2425,
        homeroom_teacher=teachers[hr_teacher_idx],
    )
    classes[class_name] = (sc, student_count, grade_num)

# ---------------------------------------------------------------------------
# Учні
# ---------------------------------------------------------------------------

print('Створення учнів...')
students_by_class = {}
used_names = set()

for class_name, (sc, student_count, grade_num) in classes.items():
    class_students = []
    last_names_pool = random.sample(LAST_NAMES, min(student_count, len(LAST_NAMES)))
    if student_count > len(LAST_NAMES):
        last_names_pool += random.choices(LAST_NAMES, k=student_count - len(LAST_NAMES))

    for j in range(student_count):
        gender = random.choice(['m', 'f'])
        first = random.choice(FIRST_NAMES_MALE if gender == 'm' else FIRST_NAMES_FEMALE)
        last = last_names_pool[j]

        # Унікальний username
        base_username = f's_{last.lower()[:6]}_{j}'
        username = base_username
        counter = 1
        while username in used_names:
            username = f'{base_username}_{counter}'
            counter += 1
        used_names.add(username)

        user = User.objects.create(
            username=username,
            password=make_password('student1234'),
            first_name=first,
            last_name=last,
            email=f'{username}@school.edu.ua',
            role='student',
        )
        student = Student.objects.create(
            user=user,
            first_name=first,
            last_name=last,
            birth_date=rnd_birth_date(grade_num),
            school_class=sc,
        )
        # Рівень учня: 20% сильних, 55% середніх, 25% слабких
        level = random.choices(['strong', 'average', 'weak'], weights=[20, 55, 25])[0]
        class_students.append((student, level))

    students_by_class[class_name] = class_students

# ---------------------------------------------------------------------------
# Призначення вчителів на предмети
# ---------------------------------------------------------------------------

print('Створення призначень вчителів...')
teacher_subjects_by_class = {}

for class_name, (sc, _, _) in classes.items():
    ts_list = []
    for subj_idx, teacher_idx in CLASS_SUBJECTS.get(class_name, []):
        ts = TeacherSubject.objects.create(
            teacher=teachers[teacher_idx],
            subject=subjects[subj_idx],
            school_class=sc,
        )
        ts_list.append(ts)
    teacher_subjects_by_class[class_name] = ts_list

# ---------------------------------------------------------------------------
# Оцінки (для 2024-2025 навчального року, обидва семестри)
# ---------------------------------------------------------------------------

print('Генерація оцінок...')

# Кількість оцінок на учня за предмет за семестр
# Залежно від предмету: точні науки — частіше перевіряємо, мистецтво — рідше
GRADES_PER_SUBJECT_SEMESTER = {
    'Математика':           (8, 14),
    'Фізика':               (6, 11),
    'Хімія':                (5, 10),
    'Біологія':             (5, 9),
    'Українська мова':      (7, 12),
    'Українська література':(5, 10),
    'Зарубіжна література': (4, 8),
    'Англійська мова':      (6, 11),
    'Географія':            (4, 8),
    'Історія України':      (5, 9),
    'Всесвітня історія':    (4, 8),
    'Інформатика':          (4, 9),
    'Фізична культура':     (3, 6),
    'Музичне мистецтво':    (2, 5),
    'Образотворче мистецтво':(2, 5),
}

# Відсоток пропусків (Н/Б) і звільнень (Зв.) на клас
NB_RATE   = 0.04   # ~4 % оцінок — відсутність
ZVIL_RATE = 0.01   # ~1 % — звільнення (фіз-ра тощо)

total_grades = 0

for class_name, (sc, _, grade_num) in classes.items():
    semesters = semesters_by_year[ay_2425.id]
    ts_list   = teacher_subjects_by_class[class_name]
    students  = students_by_class[class_name]

    for ts in ts_list:
        subj_name = ts.subject.name
        min_g, max_g = GRADES_PER_SUBJECT_SEMESTER.get(subj_name, (4, 8))

        for sem in semesters:
            # Дати оцінок рівномірно розподілені по семестру
            delta_days = (sem.end_date - sem.start_date).days
            grade_days = sorted(random.sample(range(delta_days), min(max_g * 2, delta_days)))

            for student, level in students:
                n_grades = random.randint(min_g, max_g)
                chosen_days = random.sample(grade_days, min(n_grades, len(grade_days)))
                chosen_days.sort()

                for day_offset in chosen_days:
                    grade_date = sem.start_date + timedelta(days=day_offset)
                    # Пропустити вихідні
                    if grade_date.weekday() >= 5:
                        grade_date += timedelta(days=7 - grade_date.weekday())

                    # Тип оцінки
                    roll = random.random()
                    if subj_name == 'Фізична культура' and roll < ZVIL_RATE * 5:
                        Grade.objects.create(
                            student=student,
                            teacher_subject=ts,
                            semester=sem,
                            value=None,
                            grade_type='Зв.',
                            grade_date=grade_date,
                        )
                    elif roll < NB_RATE:
                        Grade.objects.create(
                            student=student,
                            teacher_subject=ts,
                            semester=sem,
                            value=None,
                            grade_type='Н/Б',
                            grade_date=grade_date,
                        )
                    else:
                        value = rnd_grade_value(level)
                        comment = ''
                        # Зрідка додаємо коментар
                        if value <= 3 and random.random() < 0.4:
                            comment = random.choice([
                                'Потребує додаткових занять',
                                'Не виконав домашнє завдання',
                                'Відмовився відповідати',
                            ])
                        elif value == 12 and random.random() < 0.3:
                            comment = random.choice([
                                'Відмінна робота!',
                                'Творчий підхід до задачі',
                                'Блискуча відповідь',
                            ])
                        Grade.objects.create(
                            student=student,
                            teacher_subject=ts,
                            semester=sem,
                            value=value,
                            grade_type='Оцінка',
                            grade_date=grade_date,
                            comment=comment,
                        )
                    total_grades += 1

# ---------------------------------------------------------------------------
# Підсумок
# ---------------------------------------------------------------------------

print('\n' + '=' * 55)
print('  Сід-файл успішно виконано!')
print('=' * 55)
print(f'  Навчальні роки : {AcademicYear.objects.count()}')
print(f'  Семестри       : {Semester.objects.count()}')
print(f'  Предмети       : {Subject.objects.count()}')
print(f'  Вчителі        : {Teacher.objects.count()}')
print(f'  Класи          : {SchoolClass.objects.count()}')
print(f'  Учні           : {Student.objects.count()}')
print(f'  Призначення    : {TeacherSubject.objects.count()}')
print(f'  Оцінки         : {Grade.objects.count()}')
print(f'  Користувачі    : {User.objects.count()}')
print('=' * 55)
print()
print('  Облікові записи для входу:')
print('  admin        / admin1234')
print('  t_moroz_t    / teacher1234   (класний кер. 5-А)')
print('  t_savchenko_l/ teacher1234   (класний кер. 7-Б)')
print('  t_petrovia_s / teacher1234   (класний кер. 9-А)')
print('  t_romanenko_i/ teacher1234   (класний кер. 9-Б)')
print('  t_yaremenko_a/ teacher1234   (класний кер. 10-А)')
print('  t_vlasenko_n / teacher1234   (класний кер. 11-А)')
print('  s_<прізвище>_<n>/ student1234  (будь-який учень)')
print('=' * 55)