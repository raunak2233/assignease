from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from .models import User, Profile, Class, ClassStudent, ProgrammingLanguage, Assignment, AssignmentQuestion, Submission, TeacherFeedback
from .serializers import RegistrationSerializer, UserSerializer, ProfileSerializer, ClassSerializer, ClassStudentSerializer, ProgrammingLanguageSerializer, AssignmentSerializer, AssignmentQuestionSerializer, SubmissionSerializer, TeacherFeedbackSerializer, ClassStudentDetailSerializer, CustomTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Assignment, ClassStudent
from rest_framework.views import APIView
from django.db.models import Exists, OuterRef
from rest_framework.decorators import action


@api_view(['GET'])
def get_student_assignments(request, student_id):
    try:
        student_classes = ClassStudent.objects.filter(student_id=student_id)
        class_ids = student_classes.values_list('class_assigned', flat=True)

        assignments = Assignment.objects.filter(class_assigned__in=class_ids)

        serialized_assignments = AssignmentSerializer(
            assignments, 
            many=True, 
            context={'student_id': student_id} 
        )

        return Response(serialized_assignments.data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


    
@api_view(['GET'])
def get_students_in_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)

    class_students = ClassStudent.objects.filter(class_assigned=class_instance)

    serializer = ClassStudentSerializer(class_students, many=True)

    return Response(serializer.data)

class AssignmentDetailView(generics.RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the tokens
        tokens = serializer.validated_data

        # Fetch the user's role
        user = serializer.user
        role = user.profile.role if hasattr(user, 'profile') else None  # Safely access the profile

        # Construct the response
        return Response({
            'refresh': tokens['refresh'],
            'access': tokens['access'],
            'role': role,  # Include the role in the response
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for this view


class RegisterView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = []
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }, status=status.HTTP_201_CREATED)


class StudentDetailView(APIView):
    def get(self, request, student_id):
        try:
            student_profile = Profile.objects.get(user_id=student_id)
            serializer = ProfileSerializer(student_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)


class StudentSubmissionsView(APIView):
    def get(self, request, student_id):
        submissions = Submission.objects.filter(student=student_id)
        if not submissions.exists():
            return Response({"message": "No submissions found for this student."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignmentByQuestionView(APIView):
    def get(self, request, question_id):
        try:
            submission = Submission.objects.get(question_id=question_id)
            assignment = submission.assignment
            serializer = AssignmentSerializer(assignment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Submission.DoesNotExist:
            return Response({"error": "Submission with this question ID not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateSubmissionStatus(APIView):
    def patch(self, request, submission_id):
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response({"detail": "Submission not found"}, status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get('status')
        if new_status not in dict(Submission.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        
        submission.status = new_status
        submission.save()
        
        return Response({"detail": "Submission status updated successfully"}, status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Class.objects.filter(teacher_id=self.request.user)

class ClassSimpleDetailView(APIView):
    def get(self, request, class_id):
        try:
            class_instance = Class.objects.only('id', 'class_name').get(id=class_id)
            return Response(
                {"id": class_instance.id, "class_name": class_instance.class_name},
                status=status.HTTP_200_OK
            )
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found."},
                status=status.HTTP_404_NOT_FOUND
            )



class JoinedClassesView(generics.ListAPIView):
    serializer_class = ClassStudentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            raise Exception("User is not authenticated")

        queryset = ClassStudent.objects.filter(student=user)
        print(f"Queryset: {queryset}")

        if not queryset.exists():
            print("No classes found for this student.") 
        else:
            print(f"Classes found: {queryset.count()}")

        return queryset

class AssignmentListView(APIView):
    def get(self, request, class_assigned_id):
        assignments = Assignment.objects.filter(class_assigned__id=class_assigned_id)
        
        if not assignments.exists():
            return Response({"detail": "No assignments found for this class ID."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class ClassStudentViewSet(viewsets.ModelViewSet):
    queryset = ClassStudent.objects.all()
    serializer_class = ClassStudentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'], url_path='students')
    
    def get_students_in_class(self, request, pk=None):
        try:
            # Filter students by class_assigned
            students = ClassStudent.objects.filter(class_assigned=pk)
            if not students.exists():
                return Response(
                    {"message": "No students found in this class."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serialize the data
            serializer = self.get_serializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            print("Error:", e)
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        print(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProgrammingLanguageViewSet(viewsets.ModelViewSet):
    queryset = ProgrammingLanguage.objects.all()
    serializer_class = ProgrammingLanguageSerializer
    permission_classes = [IsAuthenticated]

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

class AssignmentQuestionViewSet(viewsets.ModelViewSet):
    queryset = AssignmentQuestion.objects.all()
    serializer_class = AssignmentQuestionSerializer
    permission_classes = [IsAuthenticated]

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = user.profile 

        if profile.role == 'teacher':
            # Fetch all submissions for the teacher
            return Submission.objects.all()

        # If the user is a student (check the profile's role)
        return Submission.objects.filter(student=user)




class TeacherFeedbackViewSet(viewsets.ModelViewSet):
    queryset = TeacherFeedback.objects.all()
    serializer_class = TeacherFeedbackSerializer
    permission_classes = [IsAuthenticated]



class DeleteClassView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, format=None):
        try:
            # Get the class by id
            class_instance = get_object_or_404(Class, pk=pk)

            if class_instance.teacher != request.user:
                return Response(
                    {"error": "You are not authorized to delete this class."},
                    status=status.HTTP_403_FORBIDDEN
                )

            class_instance.delete()
            return Response({"message": "Class deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
@api_view(['GET'])
def student_performance(request, student_id):
    try:
        # Total assignments assigned
        assigned_classes = ClassStudent.objects.filter(student_id=student_id).values_list("class_assigned", flat=True)
        total_assignments = Assignment.objects.filter(class_assigned__in=assigned_classes).count()

        # Submissions breakdown
        submissions = Submission.objects.filter(student_id=student_id)
        submitted_count = submissions.count()
        checked_count = submissions.filter(status="checked").count()
        reassigned_count = submissions.filter(status="reassigned").count()
        rejected_count = submissions.filter(status="rejected").count()

        performance_data = {
            "total_assignments": total_assignments,
            "submitted": submitted_count,
            "checked": checked_count,
            "reassigned": reassigned_count,
            "rejected": rejected_count,
        }

        return Response(performance_data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)        