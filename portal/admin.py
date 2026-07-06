from django.contrib import admin
from .models import (
    Subject, StudentProfile, FacultyProfile, Assignment,
    Question, Choice, Submission, Answer, Evaluation
)

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'assignment', 'question_type')
    list_filter = ('question_type', 'assignment')
    inlines = [ChoiceInline]

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'due_date', 'created_by', 'is_published')
    list_filter = ('subject', 'is_published', 'due_date')
    inlines = [QuestionInline]

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'answer_text')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_date', 'status')
    list_filter = ('status', 'assignment', 'submitted_date')
    inlines = [AnswerInline]

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_no', 'branch', 'semester', 'password')
    search_fields = ('user__username', 'roll_no', 'branch')

class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'password')
    search_fields = ('user__username', 'branch')

admin.site.register(Subject)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(FacultyProfile, FacultyProfileAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Answer)
admin.site.register(Evaluation)
