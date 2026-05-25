from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AcademicYear, Semester, Teacher, Subject, SchoolClass, Student, TeacherSubject, Grade

# Налаштування для нашої розширеної моделі User (щоб можна було призначати ролі)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    # Додаємо поле 'role' у форму редагування користувача
    fieldsets = UserAdmin.fieldsets + (
        ('Роль у системі', {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)

# Налаштування відображення інших моделей
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'academic_year', 'start_date', 'end_date')
    list_filter = ('academic_year',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'phone')
    search_fields = ('last_name', 'first_name', 'email')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_number', 'academic_year', 'homeroom_teacher')
    list_filter = ('academic_year', 'grade_number')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'school_class', 'birth_date')
    list_filter = ('school_class',)
    search_fields = ('last_name', 'first_name')

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'teacher')
    list_filter = ('school_class', 'subject')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher_subject', 'value', 'grade_type', 'grade_date')
    list_filter = ('grade_type', 'grade_date', 'semester')
    search_fields = ('student__last_name', 'student__first_name')