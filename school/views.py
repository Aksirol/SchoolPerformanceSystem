from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
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