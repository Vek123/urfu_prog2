from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Student(models.Model):
    # Первичный ключ id создаётся Django автоматически.
    name = models.CharField('Имя', max_length=15)
    surname = models.CharField('Фамилия', max_length=25)
    faculty = models.CharField('Факультет', max_length=20)
    age = models.PositiveSmallIntegerField(
        'Возраст', validators=[MinValueValidator(1), MaxValueValidator(120)])

    class Meta:
        db_table = 'students'
        ordering = ['id']
        constraints = [models.CheckConstraint(
            condition=models.Q(age__gte=1, age__lte=120),
            name='student_age_1_120')]


class Discipline(models.Model):
    # Самостоятельный справочник учебных дисциплин.
    name = models.CharField('Название', max_length=100)
    faculty = models.CharField('Факультет', max_length=20)
    hours = models.PositiveSmallIntegerField(
        'Количество часов', validators=[MinValueValidator(1), MaxValueValidator(10000)])

    class Meta:
        db_table = 'disciplines'
        ordering = ['id']
        constraints = [models.CheckConstraint(
            condition=models.Q(hours__gte=1, hours__lte=10000),
            name='discipline_hours_1_10000')]


class StudyGroup(models.Model):
    name = models.CharField('Номер группы', max_length=32, unique=True)
    faculty = models.CharField('Факультет', max_length=20)
    course = models.PositiveSmallIntegerField(
        'Курс', validators=[MinValueValidator(1), MaxValueValidator(6)])

    class Meta:
        db_table = 'study_groups'
        ordering = ['name', 'id']
        constraints = [models.CheckConstraint(
            condition=models.Q(course__gte=1, course__lte=6),
            name='study_group_course_1_6')]
