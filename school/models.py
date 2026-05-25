from django.db import models
from django.contrib.auth.models import AbstractUser


# 1. Модель користувача (USERS)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Адміністратор'),
        ('teacher', 'Вчитель'),
        ('homeroom', 'Класний керівник'),
        ('student', 'Учень / Батьки'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # Замість person_id на стороні User (як в ER), у Django правильніше
    # робити зворотний зв'язок (OneToOne) з боку Вчителя чи Учня.


# 2. Навчальні роки (ACADEMIC_YEARS)
class AcademicYear(models.Model):
    name = models.CharField(max_length=50, help_text="Наприклад: 2023-2024")
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


# 3. Семестри (SEMESTERS)
class Semester(models.Model):
    number = models.IntegerField(help_text="1 або 2")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.number} семестр ({self.academic_year.name})"


# 4. Вчителі (TEACHERS)
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


# 5. Предмети (SUBJECTS)
class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# 6. Класи (CLASSES)
class SchoolClass(models.Model):  # Названо SchoolClass, щоб не конфліктувати з ключовим словом class у Python
    name = models.CharField(max_length=10, help_text="Наприклад: 10-А")
    grade_number = models.IntegerField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    homeroom_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='homeroom_classes')

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


# 7. Учні (STUDENTS)
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


# 8. Призначення вчителів на предмети в класах (TEACHER_SUBJECTS)
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject.name} - {self.school_class.name} ({self.teacher.last_name})"


# 9. Оцінки (GRADES)
class Grade(models.Model):
    GRADE_TYPES = (
        ('Оцінка', 'Числова оцінка'),
        ('Н/Б', 'Не був'),
        ('Зв.', 'Звільнений'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    value = models.IntegerField(null=True, blank=True, help_text="Від 1 до 12")
    grade_type = models.CharField(max_length=10, choices=GRADE_TYPES, default='Оцінка')
    grade_date = models.DateField()
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.grade_type == 'Оцінка':
            return f"{self.student.last_name}: {self.value}"
        return f"{self.student.last_name}: {self.grade_type}"