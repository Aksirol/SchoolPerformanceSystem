import csv
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Avg
from django.shortcuts import render
from functools import wraps
import json

from .models import TeacherSubject, Grade, Student, Semester, SchoolClass
from .forms import GradeForm


# Декоратор для розмежування прав доступу (для вчителів ТА класних керівників)
def teacher_required(function):
    @wraps(function)           # ← додати цей рядок
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['teacher', 'homeroom']:
            return function(request, *args, **kwargs)
        raise PermissionDenied("Доступ дозволено лише вчителям та класним керівникам.")
    return wrap


@login_required
@teacher_required
def teacher_dashboard(request):
    """Повертає список предметів та класів, які викладає вчитель"""
    teacher = request.user.teacher_profile
    assignments = TeacherSubject.objects.filter(teacher=teacher).select_related('school_class', 'subject')

    data = [{"assignment_id": a.id, "class": a.school_class.name, "subject": a.subject.name} for a in assignments]
    return JsonResponse({"assignments": data})


@login_required
@teacher_required
def add_grade(request, assignment_id, student_id, semester_id):
    """T1: Виставлення оцінки вчителем. Оцінка зберігається в базі даних з прив'язкою до предмета, класу, учня та вчителя."""
    # Перевіряємо, чи має право цей вчитель виставляти оцінку цьому класу
    assignment = get_object_or_404(TeacherSubject, id=assignment_id, teacher=request.user.teacher_profile)
    student = get_object_or_404(Student, id=student_id, school_class=assignment.school_class)
    semester = get_object_or_404(Semester, id=semester_id)

    if request.method == 'POST':
        # Завантажуємо дані з JSON (оскільки працюємо як API)
        try:
            data = json.loads(request.body)
            form = GradeForm(data)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Неправильний формат даних"}, status=400)

        if form.is_valid():
            grade = form.save(commit=False)
            grade.student = student
            grade.teacher_subject = assignment
            grade.semester = semester
            grade.save()  # Оцінка зберігається в БД
            return JsonResponse({"status": "success", "message": "Оцінку успішно збережено", "grade_id": grade.id})
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    return JsonResponse({"status": "ready", "message": "Надішліть POST запит для збереження оцінки"})


# Декоратор для розмежування прав доступу (тільки для учнів/батьків)
def student_required(function):
    @wraps(function)           # ← і тут теж
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'student':
            return function(request, *args, **kwargs)
        raise PermissionDenied("Доступ дозволено лише учням та їхнім батькам.")
    return wrap


@login_required
@student_required
def student_dashboard(request):
    """U1: Перегляд власних оцінок та середнього балу учня"""
    # Знаходимо профіль учня, який прив'язаний до поточного користувача
    student = get_object_or_404(Student, user=request.user)

    # Витягуємо всі оцінки учня з прив'язкою до предметів
    grades = Grade.objects.filter(student=student).select_related('teacher_subject__subject', 'semester')

    # Розраховуємо середній бал тільки для числових оцінок (ігноруємо 'Н/Б', 'Зв.')
    numeric_grades = grades.filter(grade_type='Оцінка', value__isnull=False)
    average_score = numeric_grades.aggregate(Avg('value'))['value__avg']

    # Формуємо список оцінок для фронтенду
    grades_data = [
        {
            "subject": g.teacher_subject.subject.name,
            "value": g.value if g.grade_type == 'Оцінка' else g.grade_type,
            "date": g.grade_date.strftime('%Y-%m-%d'),
            "comment": g.comment
        } for g in grades
    ]

    return JsonResponse({
        "student_name": f"{student.first_name} {student.last_name}",
        "class": student.school_class.name,
        "average_score": round(average_score, 2) if average_score else None,
        "grades": grades_data
    })

@login_required
@teacher_required
def teacher_page(request):
    """Відображення HTML-сторінки для вчителя"""
    return render(request, 'school/teacher_page.html')

@login_required
@student_required
def student_page(request):
    """Відображення HTML-сторінки для учня"""
    return render(request, 'school/student_page.html')

@login_required
@teacher_required
def homeroom_page(request):
    """Відображення окремої HTML-сторінки для класного керівника (K1)"""
    return render(request, 'school/homeroom_page.html')


@login_required
@teacher_required
def get_journal_data(request, assignment_id):
    """Повертає список учнів та семестрів для обраного предмета/класу"""
    assignment = get_object_or_404(TeacherSubject, id=assignment_id, teacher=request.user.teacher_profile)

    # Витягуємо учнів цього класу
    students = [{"id": s.id, "name": f"{s.last_name} {s.first_name}"}
                for s in assignment.school_class.students.all().order_by('last_name')]

    # Витягуємо семестри для поточного навчального року
    semesters = [{"id": sem.id, "name": f"{sem.number} семестр"}
                 for sem in Semester.objects.filter(academic_year=assignment.school_class.academic_year)]

    return JsonResponse({"students": students, "semesters": semesters})


@login_required
@teacher_required
def export_grades_csv(request, assignment_id):
    """T3: Формування звіту успішності по предмету у форматі CSV"""
    assignment = get_object_or_404(TeacherSubject, id=assignment_id, teacher=request.user.teacher_profile)

    # Створюємо HTTP відповідь з типом контенту CSV
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig')  # utf-8-sig для коректного відображення кирилиці в Excel
    response[
        'Content-Disposition'] = f'attachment; filename="Zvit_{assignment.school_class.name}_{assignment.subject.name}.csv"'

    writer = csv.writer(response, delimiter=';')
    # Заголовки колонок
    writer.writerow(['ПІБ Учня', 'Дата', 'Оцінка/Статус', 'Семестр', 'Коментар'])

    grades = Grade.objects.filter(teacher_subject=assignment).select_related('student', 'semester').order_by(
        'student__last_name', 'grade_date')

    for grade in grades:
        student_name = f"{grade.student.last_name} {grade.student.first_name}"
        value = grade.value if grade.grade_type == 'Оцінка' else grade.grade_type
        writer.writerow([
            smart_str(student_name),
            grade.grade_date.strftime('%d.%m.%Y'),
            value,
            grade.semester.number,
            smart_str(grade.comment or '')
        ])

    return response


@login_required
@teacher_required
def homeroom_dashboard_api(request):
    """K1: Перегляд зведеної успішності класу для класного керівника"""
    teacher = request.user.teacher_profile
    # Шукаємо клас, де цей вчитель є керівником
    school_class = SchoolClass.objects.filter(homeroom_teacher=teacher).first()

    if not school_class:
        return JsonResponse({"status": "error", "message": "Ви не є класним керівником жодного класу."}, status=403)

    students = Student.objects.filter(school_class=school_class).order_by('last_name')
    report_data = []

    for student in students:
        # Отримуємо всі оцінки учня
        grades = Grade.objects.filter(student=student, grade_type='Оцінка', value__isnull=False)
        avg_score = grades.aggregate(Avg('value'))['value__avg']

        report_data.append({
            "student_name": f"{student.last_name} {student.first_name}",
            "average_score": round(avg_score, 2) if avg_score else "Немає оцінок",
            "total_grades_count": grades.count()
        })

    return JsonResponse({
        "status": "success",
        "class_name": school_class.name,
        "students": report_data
    })


@login_required
@teacher_required
def edit_grade(request, grade_id):
    """T2: Редагування раніше виставленої оцінки"""
    # Перевіряємо, чи належить оцінка вчителю, який робить запит
    grade = get_object_or_404(Grade, id=grade_id, teacher_subject__teacher=request.user.teacher_profile)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = GradeForm(data, instance=grade)
            if form.is_valid():
                form.save()
                return JsonResponse({"status": "success", "message": "Оцінку успішно оновлено"})
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Неправильний формат даних"}, status=400)

    return JsonResponse({"status": "error", "message": "Метод не підтримується"}, status=405)


@login_required
@teacher_required
def delete_grade(request, grade_id):
    """T2: Видалення оцінки"""
    # Перевіряємо права на видалення
    grade = get_object_or_404(Grade, id=grade_id, teacher_subject__teacher=request.user.teacher_profile)

    if request.method in ['DELETE', 'POST']:
        grade.delete()
        return JsonResponse({"status": "success", "message": "Оцінку успішно видалено"})

    return JsonResponse({"status": "error", "message": "Метод не підтримується"}, status=405)