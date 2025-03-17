from rest_framework import serializers
from .models import Profile, Class, ClassStudent, ProgrammingLanguage, Assignment, AssignmentQuestion, Submission, TeacherFeedback
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        try:
            profile = user.profile
            token['role'] = profile.role
        except Profile.DoesNotExist:
            token['role'] = None  

        return token
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Create user
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class RegistrationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Profile.USER_ROLES)
    name = serializers.CharField(max_length=255)
    enrollment_number = serializers.CharField(max_length=50, required=False)
    tid = serializers.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'name', 'enrollment_number', 'tid']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data): 
        # Extract profile-related fields
        role = validated_data.pop('role')
        name = validated_data.pop('name')
        enrollment_number = validated_data.pop('enrollment_number', None)
        tid = validated_data.pop('tid', None)

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()

        Profile.objects.create(
            user=user,
            role=role,
            name=name,
            enrollment_number=enrollment_number,
            tid=tid,
        )

        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'name', 'enrollment_number', 'tid']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = instance.user
        representation['username'] = user.username
        representation['email'] = user.email
        return representation


class ClassSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Class
        fields = ['id', 'class_name', 'teacher', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        if 'teacher' not in validated_data:
            validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)

class ClassStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.profile.name", read_only=True)
    enrollment_number = serializers.CharField(source="student.profile.enrollment_number", read_only=True)
    class_name = serializers.CharField(source="class_assigned.class_name", read_only=True)
    class_assigned = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), write_only=True)

    class Meta:
        model = ClassStudent
        fields = ['id', 'student', 'class_assigned', 'class_name', 'student_name', 'enrollment_number']

    def validate(self, data):
        student = data.get('student')
        class_assigned = data.get('class_assigned')
        if ClassStudent.objects.filter(student=student, class_assigned=class_assigned).exists():
            raise serializers.ValidationError("This student is already assigned to this class.")
        return data


class ClassStudentDetailSerializer(serializers.ModelSerializer):
    class_assigned = serializers.StringRelatedField()

    class Meta:
        model = ClassStudent
        fields = ['id', 'student', 'class_assigned']

class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguage
        fields = '__all__'
 
class AssignmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentQuestion
        fields = ['id', 'question_text','assignment', 'created_at']

class AssignmentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_assigned.class_name', read_only=True)
    questions = AssignmentQuestionSerializer(many=True, read_only=True, source='assignmentquestion_set')
    is_submitted = serializers.SerializerMethodField()
    language_name = serializers.CharField(source="language.language_name", read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'class_name', 'questions', 'class_assigned', 'teacher', 'language','language_name', 'is_submitted']

    def get_is_submitted(self, obj):
        student_id = self.context.get('student_id', None)
        if not student_id:
            return False  
        
        return Submission.objects.filter(assignment=obj, student_id=student_id).exists()
  

class SubmissionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="assignment.title", read_only=True)
    subject = serializers.CharField(source="assignment.class_assigned.class_name", read_only=True)
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    question = serializers.PrimaryKeyRelatedField(queryset=AssignmentQuestion.objects.all())
    questiontext = serializers.CharField(source="question.question_text", read_only=True)

    class Meta:
        model = Submission
        fields = ['id', 'title', 'subject', 'assignment', 'student', 'question', 'questiontext', 'code', 'status', 'feedback', 'submitted_at', 'updated_at']
        read_only_fields = ['submitted_at', 'updated_at']

    def create(self, validated_data):
        if 'student' not in validated_data:
            validated_data['student'] = self.context['request'].user
        return Submission.objects.create(**validated_data)


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    submission = serializers.PrimaryKeyRelatedField(queryset=Submission.objects.all())
    teacher = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = TeacherFeedback
        fields = ['id', 'submission', 'teacher', 'feedback', 'resubmission_requested', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        if 'teacher' not in validated_data:
            validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)
