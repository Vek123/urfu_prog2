from django import forms

from .models import Student, StudyGroup


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('name', 'surname', 'faculty', 'age')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'faculty': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120, 'step': 1}),
        }


class StudyGroupForm(forms.ModelForm):
    class Meta:
        model = StudyGroup
        fields = ('name', 'faculty', 'course')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6, 'step': 1}),
        }
