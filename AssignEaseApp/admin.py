from django.contrib import admin
from .models import Profile, Class, ClassStudent, ProgrammingLanguage, Assignment, AssignmentQuestion, Submission, TeacherFeedback

admin.site.register(Profile)
admin.site.register(Class)
admin.site.register(ClassStudent)
admin.site.register(ProgrammingLanguage)
admin.site.register(Assignment)
admin.site.register(AssignmentQuestion)
admin.site.register(Submission)
admin.site.register(TeacherFeedback)
