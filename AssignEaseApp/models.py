from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint

class Profile(models.Model):
    USER_ROLES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=USER_ROLES)
    name = models.CharField(max_length=255, null=True, blank=True)
    enrollment_number = models.CharField(max_length=50, null=True, blank=True)
    tid = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"    

class Class(models.Model):
    class_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming the user is a teacher
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.class_name


class ClassStudent(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['student', 'class_assigned'], name='unique_student_class')
        ]

    def __str__(self):
        return f"{self.student.username} - {self.class_assigned.class_name}"

class ProgrammingLanguage(models.Model):
    language_name = models.CharField(max_length=50)

    def __str__(self):
        return self.language_name


class Assignment(models.Model):
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title 
    
    def is_submitted(self):

        return Submission.objects.filter(assignment=self).exists()


class AssignmentQuestion(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question {self.id} for {self.assignment.title}"


class Submission(models.Model):

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('checked', 'Checked'),
        ('reassigned', 'Reassigned'),
        ('rejected', 'Rejected'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(AssignmentQuestion, on_delete=models.CASCADE)
    code = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'assignment', 'question') 








class TeacherFeedback(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    resubmission_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.submission} by {self.teacher.username}"

