from django import forms
from .models import Grade


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['value', 'grade_type', 'grade_date', 'comment']

    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get('value')
        grade_type = cleaned_data.get('grade_type')

        # Валідація 12-бальної шкали
        if grade_type == 'Оцінка':
            if value is None or value < 1 or value > 12:
                self.add_error('value', 'Оцінка повинна бути від 1 до 12 балів.')

        # Якщо учня не було або він звільнений, числова оцінка не зберігається
        if grade_type in ['Н/Б', 'Зв.']:
            cleaned_data['value'] = None

        return cleaned_data