from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import AcademicYear, Semester, Teacher, Subject, SchoolClass, Student, TeacherSubject, Grade
import datetime
from django.urls import reverse
from django.test import Client

User = get_user_model()


class DatabaseModelsTest(TestCase):
    def setUp(self):
        # 1. Створюємо користувача-вчителя
        self.user_teacher = User.objects.create_user(
            username='ivanov',
            password='testpassword123',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.user_teacher,
            first_name='Іван',
            last_name='Іванов',
            email='ivanov@school.com'
        )

        # 2. Створюємо навчальний рік та семестр
        self.year = AcademicYear.objects.create(
            name='2023-2024',
            start_date=datetime.date(2023, 9, 1),
            end_date=datetime.date(2024, 5, 31)
        )
        self.semester = Semester.objects.create(
            number=1,
            academic_year=self.year,
            start_date=datetime.date(2023, 9, 1),
            end_date=datetime.date(2023, 12, 24)
        )

        # 3. Створюємо клас та учня
        self.school_class = SchoolClass.objects.create(
            name='10-А',
            grade_number=10,
            academic_year=self.year,
            homeroom_teacher=self.teacher
        )
        self.student = Student.objects.create(
            first_name='Петро',
            last_name='Петренко',
            birth_date=datetime.date(2008, 5, 15),
            school_class=self.school_class
        )

        # 4. Створюємо предмет та призначення
        self.subject = Subject.objects.create(name='Математика')
        self.teacher_subject = TeacherSubject.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            school_class=self.school_class
        )

    def test_student_creation_and_relations(self):
        """Перевіряємо, чи учень правильно прив'язаний до класу"""
        self.assertEqual(self.student.school_class.name, '10-А')
        self.assertEqual(self.student.school_class.homeroom_teacher.last_name, 'Іванов')

    def test_grade_assignment(self):
        """Перевіряємо процес виставлення оцінки учню"""
        grade = Grade.objects.create(
            student=self.student,
            teacher_subject=self.teacher_subject,
            semester=self.semester,
            value=11,
            grade_type='Оцінка',
            grade_date=datetime.date(2023, 10, 15)
        )

        self.assertEqual(Grade.objects.count(), 1)
        self.assertEqual(grade.value, 11)
        self.assertEqual(grade.student.first_name, 'Петро')

    def test_absent_grade_type(self):
        """Перевіряємо виставлення статусу 'Н/Б' (не був)"""
        grade_absent = Grade.objects.create(
            student=self.student,
            teacher_subject=self.teacher_subject,
            semester=self.semester,
            grade_type='Н/Б',
            grade_date=datetime.date(2023, 10, 16)
        )
        self.assertEqual(grade_absent.value, None)
        self.assertEqual(grade_absent.grade_type, 'Н/Б')


class AdminPanelTest(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Створюємо суперкористувача (Адміністратора) з усіма правами
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='adminpassword123',
            role='admin'
        )

        # 2. Створюємо звичайного користувача (Учня) без прав доступу
        self.regular_user = User.objects.create_user(
            username='student_test',
            password='studentpassword123',
            role='student'
        )

    def test_admin_access_for_superuser(self):
        """Перевірка, що суперкористувач має доступ до головної сторінки адмін-панелі"""
        self.client.login(username='admin_test', password='adminpassword123')
        response = self.client.get(reverse('admin:index'))

        # Очікуємо статус 200 (OK - сторінка успішно завантажена)
        self.assertEqual(response.status_code, 200)

    def test_admin_access_denied_for_regular_user(self):
        """Перевірка, що звичайний користувач НЕ має доступу до адмін-панелі"""
        self.client.login(username='student_test', password='studentpassword123')
        response = self.client.get(reverse('admin:index'))

        # Очікуємо статус 302 (Found/Redirect) - система повинна "викинути"
        # користувача і перенаправити його на сторінку введення логіну адмінки
        self.assertEqual(response.status_code, 302)

    def test_admin_pages_load(self):
        """Перевірка завантаження сторінок управління моделями (A1, A2)"""
        self.client.login(username='admin_test', password='adminpassword123')

        # Перевіряємо сторінку управління користувачами (A1: Реєстрація користувача)
        response_users = self.client.get(reverse('admin:school_user_changelist'))
        self.assertEqual(response_users.status_code, 200)

        # Перевіряємо сторінку управління предметами (A2: Налаштування класів і предметів)
        response_subjects = self.client.get(reverse('admin:school_subject_changelist'))
        self.assertEqual(response_subjects.status_code, 200)

        # Перевіряємо сторінку управління класами
        response_classes = self.client.get(reverse('admin:school_schoolclass_changelist'))
        self.assertEqual(response_classes.status_code, 200)

    def test_create_subject_via_admin(self):
        """Перевірка реального створення об'єкта (Предмета) через POST-запит адмінки"""
        self.client.login(username='admin_test', password='adminpassword123')

        # URL для сторінки "Додати предмет"
        url = reverse('admin:school_subject_add')

        # Імітуємо заповнення форми і натискання кнопки "Зберегти"
        data = {
            'name': 'Фізика',
            'description': 'Курс фізики для старших класів'
        }
        response = self.client.post(url, data)

        # Після успішного збереження Django робить редірект назад до списку
        self.assertEqual(response.status_code, 302)

        # Перевіряємо, чи фізично з'явився предмет "Фізика" у базі даних
        self.assertTrue(Subject.objects.filter(name='Фізика').exists())