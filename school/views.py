from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Avg
from django.shortcuts import render
import json

from .models import TeacherSubject, Grade, Student, Semester
from .forms import GradeForm


# Декоратор для розмежування прав доступу (тільки для вчителів)
def teacher_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'teacher':
            return function(request, *args, **kwargs)
        raise PermissionDenied("Доступ дозволено лише вчителям.")

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