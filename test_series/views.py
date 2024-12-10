import json
from django.shortcuts import get_object_or_404 # type: ignore
from django.http import JsonResponse # type: ignore
from django.utils import timezone # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.views.decorators.http import require_POST, require_GET # type: ignore
from django.views.decorators.http import require_http_methods
from .models import  Notification, Notification2, ProctoringEvent, ProctoringSession, Exam, Question, UserResponse, UserScore,Notification1,Notification3
from .forms import ExamParticipantForm, MarkAsReadForm, MarkAsReadForm2, MarkAsReadForm3, MarkForReviewForm, NotificationForm, NotificationForm2, StartProctoringSessionForm, EndProctoringSessionForm, RecordProctoringEventForm, SubmitAllAnswersForm, SubmitAnswerForm,MarkAsReadForm1,NotificationForm1,NotificationForm3
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views import View
# from django.db.models import Q
from .models import new_user, JobSeeker, CompanyInCharge, UniversityInCharge


def api_response(success, data=None, error=None, details=None, status=200):
    try:
        response = {'success': success}
        if data:
            response['data'] = data
        if error:
            response['error'] = error
        if details:
            response['details'] = details
        return JsonResponse(response, status=status)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StartProctoringSessionView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            form = StartProctoringSessionForm(json.loads(request.body.decode('utf-8')))
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid data'}, status=400)

            exam_id = form.cleaned_data['exam_id']
            duration = form.cleaned_data.get('duration', timezone.timedelta(hours=3))

            user = new_user.objects.filter(token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            exam = get_object_or_404(Exam, id=exam_id)
            if ProctoringSession.objects.filter(user=user, exam=exam).exists():
                return JsonResponse({'error': 'Proctoring session for this exam already exists'}, status=400)

            session = ProctoringSession.objects.create(
                user=user,
                exam=exam,
                start_time=timezone.now(),
                duration=duration,
                status='ongoing'
            )

            return JsonResponse({'success': True, 'session_id': session.id}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred', 'details': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class EndProctoringSessionView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            form = EndProctoringSessionForm(json.loads(request.body.decode('utf-8')))
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid data'}, status=400)

            user = new_user.objects.filter(token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            session_id = form.cleaned_data['session_id']
            session = get_object_or_404(ProctoringSession, id=session_id, user=user)

            session.end_time = timezone.now()
            session.status = 'completed'
            session.save()

            user_email = user.email
            try:
                send_mail(
                    "Proctoring Event Notification",
                    "Session ended",
                    settings.EMAIL_HOST_USER,
                    [user_email]
                )
            except Exception as email_error:
                return JsonResponse({
                    'success': True,
                    'data': {'status': 'completed'},
                    'error': f'Failed to send email to {user_email}',
                    'details': str(email_error)
                }, status=500)

            return JsonResponse({'success': True, 'data': {'status': 'completed'}}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while ending the session', 'details': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RecordProctoringEventView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            user = new_user.objects.filter(token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            form = RecordProctoringEventForm(json.loads(request.body.decode('utf-8')))
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid data'}, status=400)

            session_id = form.cleaned_data['session_id']
            session = get_object_or_404(ProctoringSession, id=session_id,user=user)

            if ProctoringEvent.objects.filter(session=session).exists():
                return JsonResponse({'error': 'Event for this session already recorded'}, status=400)

            event = form.save(commit=False)
            event.session = session
            event.save()

            user_email = user.email
            try:
                send_mail(
                    "Proctoring Event Notification",
                    "Event recorded",
                    settings.EMAIL_HOST_USER,
                    [user_email]
                )
            except Exception as email_error:
                return JsonResponse({
                    'success': True,
                    'data': {'status': 'event recorded'},
                    'error': 'Failed to send email notification',
                    'details': str(email_error)
                }, status=500)

            return JsonResponse({'success': True, 'data': {'status': 'event recorded'}}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while recording the event', 'details': str(e)}, status=500)

@csrf_exempt
@require_POST
def submit_answer(request):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return api_response({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return api_response({'error': 'Invalid token'}, status=403)

        form = SubmitAnswerForm(json.loads(request.body))
        if not form.is_valid():
            return api_response(success=False, error='Invalid data', status=400)

        session_id = form.cleaned_data['session_id']
        session = get_object_or_404(ProctoringSession.objects.only('id', 'exam'), id=session_id, user=user)

        question_no = form.cleaned_data['question_no']
        selected_option = form.cleaned_data['selected_option']
        clear_response = form.cleaned_data['clear_response']

        question = get_object_or_404(Question.objects.only('id', 'status', 'correct_option'), exam=session.exam, question_no=question_no)

        user_response = UserResponse.objects.filter(user=user, question=question, session=session).first()
        if clear_response:
            if user_response:
                if user_response.selected_option == question.correct_option:
                    user_score, _ = UserScore.objects.get_or_create(user=user, exam=session.exam)
                    if user_score.score > 0:
                        user_score.score -= 1
                        user_score.save(update_fields=['score'])

                user_response.delete()
            return api_response(success=True, data={'message': 'Response cleared and score updated.'})

        if user_response:
            return api_response(success=False, error='Answer already submitted', status=400)

        UserResponse.objects.create(
            user=user,
            question=question,
            session=session,
            selected_option=selected_option,
            response_time=timezone.now()
        )

        if question.status != 'Answered':
            question.status = 'Answered'
            question.save(update_fields=['status'])

        if selected_option == question.correct_option:
            user_score, _ = UserScore.objects.get_or_create(user=user, exam=session.exam)
            user_score.score += 1
            user_score.save(update_fields=['score'])

        return api_response(success=True, data={'message': 'Answer submitted successfully'})

    except Exception as e:
        return api_response(success=False, error='An error occurred while submitting the answer', details=str(e), status=500)

# @method_decorator(csrf_exempt, name='dispatch')
# @require_GET
# def get_session_status(request, session_id):
#     try:
#         auth_header = request.headers.get('Authorization', '')
#         token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

#         if not token:
#             return JsonResponse({'error': 'Token is required'}, status=400)

#         user = new_user.objects.filter(token=token).first()
#         if not user:
#             return JsonResponse({'error': 'Invalid token'}, status=403)

#         session = get_object_or_404(ProctoringSession, id=session_id, user=user)

#         questions = session.exam.questions.all()
#         total_questions = questions.count()
#         answered_questions = questions.filter(status="Answered").count()
#         not_answered_questions = questions.filter(status="Not Answered").count()
#         marked_for_review = questions.filter(status="Mark for Review").count()
#         not_visited_questions = questions.filter(status="Not Visited").count()

#         remaining_time = session.duration - (timezone.now() - session.start_time)

#         status = {
#             'answered_questions': answered_questions,
#             'not_answered_questions': not_answered_questions,
#             'marked_for_review': marked_for_review,
#             'not_visited_questions': not_visited_questions,
#             'remaining_time': remaining_time.total_seconds(),
#             'total_questions': total_questions,
#         }

#         return api_response(status, status=200)

#     except Exception as e:
#         return api_response({'error': 'An error occurred while fetching session status',
#                              'details': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@require_GET
def get_question_details(request, session_id, question_no):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        session = get_object_or_404(ProctoringSession, id=session_id, user=user)
        question = get_object_or_404(Question, exam=session.exam, question_no=question_no)

        response_data = {
            'question_no': question.question_no,
            'question_text': question.question_text,
            'option1': question.option1,
            'option2': question.option2,
            'option3': question.option3,
            'option4': question.option4,
            'status': question.status,
            'section': question.section,
        }

        return api_response(success=True, data=response_data)

    except Exception as e:
        return api_response(
            success=False,
            error='An error occurred while fetching the question details',
            details=str(e),
            status=500
        )

# @method_decorator(csrf_exempt, name='dispatch')
# @require_GET
# def count_questions(request, exam_id):
#     try:
#         auth_header = request.headers.get('Authorization', '')
#         token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

#         if not token:
#             return JsonResponse({'error': 'Token is required'}, status=400)

#         user = new_user.objects.filter(token=token).first()
#         if not user:
#             return JsonResponse({'error': 'Invalid token'}, status=403)

#         exam = Exam.objects.filter(id=exam_id).only('id', 'name').first()
#         if not exam:
#             return api_response(success=False, error='Exam ID not found', status=404)

#         question_count = Question.objects.filter(exam=exam).count()

#         if not question_count:
#             return api_response(success=False, error='No Questions found for this Exam', data={'exam_name': exam.name}, status=404)

#         return api_response(success=True, data={'question_count': question_count, 'exam_name': exam.name})

#     except Exception as e:
#         return api_response(success=False, error='An error occurred while counting questions', details=str(e), status=500)

@csrf_exempt
@require_POST
def mark_for_review(request):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        form = MarkForReviewForm(json.loads(request.body))
        if not form.is_valid():
            return api_response(success=False, error='Invalid data', status=400)

        session_id = form.cleaned_data['session_id']
        question_no = form.cleaned_data['question_no']
        mark = form.cleaned_data['mark']

        session = get_object_or_404(ProctoringSession.objects.only('id', 'exam'), id=session_id,  user=user)
        question = get_object_or_404(Question.objects.only('id', 'status'), exam=session.exam, question_no=question_no)

        new_status = 'Mark for Review' if mark else 'Not Answered'
        if question.status != new_status:
            question.status = new_status
            question.save(update_fields=['status'])

        message = 'Question marked for review' if mark else 'Mark for review removed'
        return api_response(success=True, data={'status': message})

    except Exception as e:
        return api_response(success=False, error='An error occurred while marking the question for review', details=str(e), status=500)

def fetch_event_types(request):
    try:
        if request.method == 'GET':
            event_types = ProctoringEvent.objects.filter(event_type__isnull=False).exclude(event_type='').values_list('event_type', flat=True).distinct()
            return api_response({'event_types': list(event_types)})
        else:
            return api_response({'status': 'error', 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return api_response({'status': 'error', 'message': str(e)}, status=500)

def fetch_section_types(request):
    try:
        if request.method == 'GET':
            section_types = Question.objects.filter(section__isnull=False).exclude(section='').values_list('section', flat=True).distinct()
            return api_response({'section_types': list(section_types)})
        else:
            return api_response({'status': 'error', 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return api_response({'status': 'error', 'message': str(e)}, status=500)

def fetch_status_types(request):
    try:
        if request.method == 'GET':
            status_types = Question.objects.filter(status__isnull=False).exclude(status='').values_list('status', flat=True).distinct()
            return api_response({'status_types': list(status_types)})
        else:
            return api_response({'status': 'error', 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return api_response({'status': 'error', 'message': str(e)}, status=500)

class StatusTypeChoicesAPIView(APIView):
    def get(self, request, fmt=None):
        try:
            session_type_choices = {key: value for key, value in ProctoringSession.STATUS_CHOICES}
            return api_response({'choices': session_type_choices}, status=200)
        except Exception as e:
            return api_response({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def get_details(request):
    if request.method == 'POST':
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is required'}, status=400)

            user = new_user.objects.filter(token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=403)

            data = json.loads(request.body)
            session_id = data.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session ID is required'}, status=400)

            session = get_object_or_404(ProctoringSession, id=session_id,user=user)
            exam = session.exam

            score = fetch_user_score(user, exam.id)

            answered_questions = exam.questions.filter(status="Answered").count()
            not_answered_questions = exam.questions.filter(status="Not Answered").count()
            not_visited_questions = exam.questions.filter(status="Not Visited").count()
            marked_for_review = exam.questions.filter(status="Mark for Review").count()

            details = {
                'Name': data.get('name', ''),
                'Phone': data.get('mobile_no', ''),
                'Email': data.get('email', ''),
                'Score': score,
                'answered_questions': answered_questions,
                'not_answered_questions': not_answered_questions,
                'marked_for_review': marked_for_review,
                'not_visited_questions': not_visited_questions,
            }

            return JsonResponse({'Quiz Summary': details}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred', 'details': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)


def fetch_user_score(user, exam_id):
    try:
        user_score = UserScore.objects.filter(user=user, exam_id=exam_id).first()
        return user_score.score if user_score else 0
    except UserScore.DoesNotExist:
        return 0

@csrf_exempt
@require_POST
def submit_all_answers(request):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return api_response({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return api_response({'error': 'Invalid token'}, status=403)

        form = SubmitAllAnswersForm(json.loads(request.body))
        if form.is_valid():
            session_id = form.cleaned_data['session_id']
            answers = form.cleaned_data['answers']

            session = get_object_or_404(ProctoringSession, id=session_id, user=user)
            user_score, _ = UserScore.objects.get_or_create(user=user, exam=session.exam)

            question_map = {q.question_no: q for q in session.exam.questions.all()}
            current_time = timezone.now()

            for answer in answers:
                question_no = answer['question_no']
                selected_option = answer['selected_option']
                question = question_map.get(question_no)

                if question:
                    _, created = UserResponse.objects.get_or_create(
                        user=user,
                        question=question,
                        session=session,
                        defaults={'selected_option': selected_option, 'response_time': current_time}
                    )
                    if created and selected_option == question.correct_option:
                        user_score.score += 1

                    question.status = 'Answered'
                    question.save()

            user_score.save()
            return api_response({'success': True, 'message': 'Go to details page'}, status=200)
        else:
            return api_response({'success': False, 'error': 'Invalid data', 'details': form.errors}, status=400)
    except Exception as e:
        return api_response({'success': False, 'error': 'An error occurred while submitting all answers', 'details': str(e)}, status=500)


@csrf_exempt
@require_GET
def get_next_question(request, session_id, current_question_no):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        session = get_object_or_404(ProctoringSession, id=session_id, user=user)

        next_question = (
            Question.objects.filter(exam=session.exam, question_no__gt=current_question_no)
            .order_by('question_no')
            .values('question_no', 'question_text', 'option1', 'option2', 'option3', 'option4', 'status', 'section')
            .first()
        )

        if not next_question:
            return JsonResponse({'success': False, 'error': 'No next question available'}, status=404)

        return JsonResponse(next_question, status=200)

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while fetching the next question', 'details': str(e)}, status=500)

@csrf_exempt
@require_GET
def get_previous_question(request, session_id, current_question_no):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        session = get_object_or_404(ProctoringSession, id=session_id, user=user)

        previous_question = (
            Question.objects.filter(exam=session.exam, question_no__lt=current_question_no)
            .order_by('-question_no')
            .values('question_no', 'question_text', 'option1', 'option2', 'option3', 'option4', 'status', 'section')
            .first()
        )

        if not previous_question:
            return JsonResponse({'success': False, 'error': 'No previous question available'}, status=404)

        return JsonResponse(previous_question, status=200)

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while fetching the previous question', 'details': str(e)}, status=500)

@csrf_exempt
@require_POST
def submit_details(request):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)

        user = new_user.objects.filter(token=token).first()
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        form = ExamParticipantForm(request.POST)
        if not form.is_valid():
            return api_response({'status': 'error', 'errors': form.errors})

        participant = form.save(commit=False)

        if participant.email != user.email:
            return JsonResponse({'status': 'error', 'message': 'Email does not match the authenticated user'}, status=403)

        participant.exam_started = True
        participant.save()

        return api_response({
            'status': 'success',
            'message': 'Exam details submitted successfully',
            'participant_id': participant.id,
            'exam_started': participant.exam_started
        })

    except Exception as e:
        return api_response({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_notifications(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = new_user.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        data = [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
        return api_response({"status": "success", "notifications": data})
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = new_user.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notification = get_object_or_404(Notification, id=notification_id, user=user)
        form = MarkAsReadForm({'is_read': True}, instance=notification)

        if form.is_valid():
            form.save()
            return api_response({"status": "success", "message": "Notification marked as read."})

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_notification(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = new_user.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        data = json.loads(request.body)
        form = NotificationForm(data)

        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = user
            notification.save()

            subject = "New Notification Created"
            message = f"A new notification has been created:\n\nTitle: {notification.title}\nMessage: {notification.message}\n\nThank you for using our service."
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return api_response({"status": "success", "message": "Notification created successfully."}, status=201)

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except json.JSONDecodeError:
        return api_response({"status": "error", "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_notifications1(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = JobSeeker.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notifications = Notification1.objects.filter(user=user).order_by('-created_at')
        data = [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
        return api_response({"status": "success", "notifications": data})
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read1(request, notification_id):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = JobSeeker.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notification = get_object_or_404(Notification1, id=notification_id, user=user)
        form = MarkAsReadForm1({'is_read': True}, instance=notification)

        if form.is_valid():
            form.save()
            return api_response({"status": "success", "message": "Notification marked as read."})

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_notification1(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = JobSeeker.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        data = json.loads(request.body)
        form = NotificationForm1(data)

        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = user
            notification.save()

            subject = "New Notification Created"
            message = f"Dear {user.first_name},\n\nYou have a new notification:\n\nTitle: {notification.title}\nMessage: {notification.message}\n\nThank you for using our service."

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return api_response({"status": "success", "message": "Notification created successfully."}, status=201)

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except json.JSONDecodeError:
        return api_response({"status": "error", "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_notifications2(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = UniversityInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notifications = Notification2.objects.filter(user=user).order_by('-created_at')
        data = [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
        return api_response({"status": "success", "notifications": data})
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read2(request, notification_id):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = UniversityInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notification = get_object_or_404(Notification2, id=notification_id, user=user)
        form = MarkAsReadForm2({'is_read': True}, instance=notification)

        if form.is_valid():
            form.save()
            return api_response({"status": "success", "message": "Notification marked as read."})

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_notification2(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = UniversityInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        data = json.loads(request.body)
        form = NotificationForm2(data)

        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = user
            notification.save()

            subject = "New Notification Created"
            message = f"A new notification has been created:\n\nTitle: {notification.title}\nMessage: {notification.message}\n\nThank you for using our service."
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.official_email],
                fail_silently=False,
            )

            return api_response({"status": "success", "message": "Notification created successfully."}, status=201)

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except json.JSONDecodeError:
        return api_response({"status": "error", "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_notifications3(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = CompanyInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notifications = Notification3.objects.filter(user=user).order_by('-created_at')
        data = [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
        return api_response({"status": "success", "notifications": data})
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read3(request, notification_id):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = CompanyInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        notification = get_object_or_404(Notification3, id=notification_id, user=user)
        form = MarkAsReadForm3({'is_read': True}, instance=notification)

        if form.is_valid():
            form.save()
            return api_response({"status": "success", "message": "Notification marked as read."})

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_notification3(request):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    if not token:
        return api_response({'error': 'Token is required'}, status=400)

    user = CompanyInCharge.objects.filter(token=token).first()
    if not user:
        return api_response({'error': 'Invalid token'}, status=403)

    try:
        data = json.loads(request.body)
        form = NotificationForm3(data)

        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = user
            notification.save()

            subject = "New Notification Created"
            message = f"A new notification has been created:\n\nTitle: {notification.title}\nMessage: {notification.message}\n\nThank you for using our service."
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.official_email],
                fail_silently=False,
            )

            return api_response({"status": "success", "message": "Notification created successfully."}, status=201)

        return api_response({"status": "error", "errors": form.errors}, status=400)
    except json.JSONDecodeError:
        return api_response({"status": "error", "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        return api_response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def lead_submission_view(request):
    try:
        if request.method == "POST":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

            form = LeadForm(data)
            if form.is_valid():
                lead = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Lead submitted successfully.",
                    "data": {
                        "id": lead.id,
                        "name": lead.name,
                        "email": lead.email,
                        "mobile": lead.mobile,
                        "page": lead.page,
                        "time_duration": lead.time_duration,
                        "approx_cost_to_invest": float(lead.approx_cost_to_invest),
                        "targeted_audience": lead.targeted_audience,
                    }
                })
            else:
                return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        else:
            return JsonResponse({"status": "error", "message": "Method not allowed."}, status=405)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def fetch_targeted_audience_choices(request):
    try:
        if request.method == 'GET':
            values_list = [choice[0] for choice in Lead.TARGETED_AUDIENCE_CHOICES]

            return JsonResponse({'status': 'success', 'choices': values_list})

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def fetch_page_choices(request):
    try:
        if request.method == 'GET':
            page_choices = Lead.PAGE_CHOICES
            values_list = [choice[0] for choice in page_choices]

            return JsonResponse({'status': 'success', 'choices': values_list})

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
