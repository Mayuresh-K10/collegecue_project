from django.http import JsonResponse # type: ignore
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from django.middleware.csrf import get_token # type: ignore
from django.views.decorators.csrf import csrf_exempt, csrf_protect # type: ignore
from .utils import (send_data_to_google_sheet3,send_data_to_google_sheet4,
send_data_to_google_sheet2,send_data_to_google_sheets)
import secrets,json,requests, os # type: ignore
from .models import CompanyInCharge, Consultant, JobSeeker, UniversityInCharge, new_user
from django.contrib.auth.hashers import make_password, check_password # type: ignore
from django.utils.decorators import method_decorator # type: ignore
from django.views import View # type: ignore
from .forms import (JobSeekerRegistrationForm, UniversityInChargeForm,CompanyInChargeForm,ForgotForm,
SubscriptionForm1,ConsultantForm,Forgot2Form
,VerifyForm,SubscriptionForm)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # type: ignore
# from django.utils.html import format_html
from django.core.mail import EmailMessage
# from django.template.loader import render_to_string
from google.oauth2 import id_token # type: ignore
from django.utils.crypto import get_random_string


#CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

#CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')


def generate_unique_token():
    return get_random_string(40)

def home(request):
    try:
        return JsonResponse({"message": "Welcome to CollegeCue!"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_csrf_token(request):
    try:
        csrf_token = get_token(request)
        return JsonResponse({'csrf_token': csrf_token}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Register(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))

            first_name = data.get('firstname')
            last_name = data.get('lastname')
            email = data.get('email')
            country_code = data.get('country_code')
            phone_number = data.get('phonenumber')
            password = data.get('password')

            if not email:
                return JsonResponse({'error': 'Please enter a correct email id'}, status=400)
            if not password:
                return JsonResponse({'error': 'Please enter password'}, status=400)

            hashed_password = make_password(password)
            send_data_to_google_sheets(first_name, last_name, email, country_code, phone_number, hashed_password, "Sheet1")
            return JsonResponse({'message': 'go to next page'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Next(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': {'json': 'Invalid JSON'}}, status=400)

        first_name = data.get('firstname')
        last_name = data.get('lastname')
        email = data.get('email')
        password = data.get('password')
        course = data.get('course')
        education = data.get('education')
        percentage = data.get('percentage')
        preferred_destination = data.get('preferred_destination')
        start_date = data.get('start_date')
        mode_study = data.get('mode_study')
        entrance_exam = data.get('entrance')
        passport = data.get('passport')
        country_code = data.get('country_code')
        phone_number = data.get('phonenumber')

        errors = {}
        if not entrance_exam:
            errors['entrance'] = 'Check box not clicked'
        if not passport:
            errors['passport'] = 'Check box not clicked'
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        try:
            new_password = make_password(password)
            try:
                us = new_user(
                    firstname=first_name, lastname=last_name, email=email,
                    country_code=country_code, phonenumber=phone_number,
                    password=new_password, course=course, educations=education,
                    percentage=percentage, preferred_destination=preferred_destination,
                    start_date=start_date, mode_study=mode_study,
                    entrance=entrance_exam, passport=passport
                )
                us.save()
                return JsonResponse({'message': 'Registration successful'})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'server': str(e)}}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': {'password': str(e)}}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Login(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email')
            password = data.get('password')

            if not email:
                return JsonResponse({'error': 'Please enter an email id'}, status=400)
            if not password:
                return JsonResponse({'error': 'Please enter a password'}, status=400)

            user = new_user.objects.filter(email=email, is_deleted=False).first()

            if not user:
                return JsonResponse({'error': 'Email id not found or user has been deleted'}, status=404)

            if not check_password(password, user.password):
                return JsonResponse({'error': 'Invalid credentials'}, status=400)

            unique_token = generate_unique_token()
            user.token = unique_token
            user.save()

            return JsonResponse({
                'message': 'Login successful',
                'unique_token': unique_token,
                'firstname':user.firstname,
                'lastname':user.lastname,
                'phone':user.phonenumber,
                'email':user.email,
                'id':user.id,
                'model':'new_user',
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Forgot_view(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            form = ForgotForm(data)

            if form.is_valid():
                forgot = form.save()
                EMAIL = forgot.email

                user = new_user.objects.filter(email=EMAIL, token=token).first()
                if not user:
                    return JsonResponse({'error': 'Invalid token or email does not exist'}, status=404)

                new_otp = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
                request.session['otp'] = new_otp
                request.session['email'] = EMAIL
                request.session.save()

                subject = 'Your One-Time Password (OTP) for Secure Access'
                message = f'''Dear User,

                For security purposes, please use the following One-Time Password (OTP) to complete your authentication:

                OTP: {new_otp}

                Please enter this OTP within the next 3 minutes to ensure successful access. If you did not request this OTP, please contact our support team immediately.

                Thank you for your attention to this matter.

                Best regards,
                Collegecue
                Support Team
                '''
                sender_email = settings.EMAIL_HOST_USER
                recipient_email = [EMAIL]

                send_mail(subject, message, sender_email, recipient_email)
                return JsonResponse({'message': 'OTP sent successfully'})
            else:
                errors = dict(form.errors.items())
                return JsonResponse({'success': False, 'errors': errors}, status=400)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Verify_view(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            form = VerifyForm(data)

            stored_email = request.session.get('email')
            user = new_user.objects.filter(email=stored_email, token=token).first()
            
            if not user:
                return JsonResponse({'error': 'Invalid token or user not found'}, status=404)
            
            if form.is_valid():
                verify = form.save()
                otp_entered = verify.otp
                stored_otp = request.session.get('otp')

                if stored_email and stored_otp:
                    if stored_otp == otp_entered:
                        del request.session['otp']
                        return JsonResponse({'message': 'OTP verification successful'})
                    else:
                        return JsonResponse({'error': 'Invalid OTP'}, status=400)
                else:
                    return JsonResponse({'error': 'Session data not found'}, status=400)
            else:
                errors = dict(form.errors.items())
                return JsonResponse({'success': False, 'errors': errors}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ResendOtpView(View):
    def get(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            csrf_token = get_token(request)
            if not csrf_token:
                return JsonResponse({'error': 'CSRF token missing'}, status=403)

            email = request.session.get('email')
            if not email:
                return JsonResponse({'error': 'Email not found in session'}, status=400)

            user = new_user.objects.filter(email=email, token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token or user not found'}, status=404)

            new_otp = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
            request.session['otp'] = new_otp

            subject = 'Your One-Time Password (OTP) for Secure Access'
            message = f'''Dear User,

            For security purposes, please use the following One-Time Password (OTP) to complete your authentication:

            OTP: {new_otp}

            Please enter this OTP within the next 3 minutes to ensure successful access. If you did not request this OTP, please contact our support team immediately.

            Thank you for your attention to this matter.

            Best regards,
            Collegecue
            Support Team
            '''
            sender_email = settings.EMAIL_HOST_USER
            recipient_email = [email]
            send_mail(subject, message, sender_email, recipient_email)

            return JsonResponse({'message': 'New OTP sent successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class Forgot2_view(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            form = Forgot2Form(data)

            if not form.is_valid():
                errors = {field: errors for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)

            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            if password != confirm_password:
                return JsonResponse({'error': 'Passwords did not match'}, status=400)
            
            stored_email = request.session.get('email')
            user = new_user.objects.filter(email=stored_email, token=token).first()

            if user:
                user.password = make_password(password)
                user.save()
                del request.session['email']
                return JsonResponse({'message': 'Password updated successfully'}, status=200)

            return JsonResponse({'error': 'Invalid token or user not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except IndexError:
            return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StudentLogoutView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to logout'}, status=400)

            student_user = new_user.objects.filter(token=token).first()
            if not student_user:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            student_user.token = None
            student_user.save()

            return JsonResponse({'success': True, 'message': 'Student logout successful'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteUserAccountView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None
            
            data = json.loads(request.body.decode('utf-8'))
            confirmation = data.get('confirmation', False)

            if not token or not confirmation:
                return JsonResponse({'error': 'Token and confirmation are required'}, status=400)

            user = new_user.objects.filter(token=token).first()
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            user.is_deleted = True
            user.token = None
            user.save()

            return JsonResponse({'success': True, 'message': 'Account deleted successfully'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



@method_decorator(csrf_exempt, name='dispatch')
class RegisterCompanyInChargeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = CompanyInChargeForm(data)
        if form.is_valid():
            company = form.save(commit=False)
            company.password = make_password(company.password)
            company.save()
            send_data_to_google_sheet2(
                company.company_name,
                company.official_email,
                company.country_code,
                company.mobile_number,
                company.password,
                company.linkedin_profile,
                company.company_person_name,
                company.agreed_to_terms,
                "Sheet2"
            )
            sender_email = settings.EMAIL_HOST_USER
            recipient_email = [company.official_email]
            subject = 'Confirmation Mail'
            # message = render_to_string('email_template.html', {'name': company.company_name})
            message = '''Dear User,

            Thank you for your registration.

            If you have any questions or need further assistance, please don't hesitate to contact our support team.

            Best regards,
            Collegecue
            Support Team
            '''
            email = EmailMessage(subject, message, sender_email, recipient_email)
            # email.content_subtype = "html"  # Main content is now text/html
            email.send()
            return JsonResponse({'success': True, 'message': 'Registration successful'})
        else:
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterUniversityInChargeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = UniversityInChargeForm(data)
        if form.is_valid():
            university = form.save(commit=False)
            university.password = make_password(university.password)
            university.save()
            send_data_to_google_sheet3(
                university.university_name,
                university.official_email,
                university.country_code,
                university.mobile_number,
                university.password,
                university.linkedin_profile,
                university.college_person_name,
                university.agreed_to_terms,
                "Sheet3"
            )
            sender_email = settings.EMAIL_HOST_USER
            recipient_email = [university.official_email]
            subject = 'Confirmation Mail'
            # message = render_to_string('email_template.html', {'name': university.university_name})
            message = '''Dear User,

            Thank you for your registration.

            If you have any questions or need further assistance, please don't hesitate to contact our support team.

            Best regards,
            Collegecue
            Support Team
            '''
            email = EmailMessage(subject, message, sender_email, recipient_email)
            # email.content_subtype = "html"
            email.send()
            return JsonResponse({'success': True, 'message': 'Registration successful'})
        else:
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterConsultantView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = ConsultantForm(data)
        if form.is_valid():
            consultant = form.save(commit=False)
            consultant.password = make_password(consultant.password)
            consultant.save()
            send_data_to_google_sheet4(
                consultant.consultant_name,
                consultant.official_email,
                consultant.country_code,
                consultant.mobile_number,
                consultant.password,
                consultant.linkedin_profile,
                consultant.consultant_person_name,
                consultant.agreed_to_terms,
                "Sheet4"
            )
            sender_email = settings.EMAIL_HOST_USER
            recipient_email = [consultant.official_email]
            subject = 'Confirmation Mail'
            # message = render_to_string('email_template.html', {'name': consultant.consultant_name})
            message = '''Dear User,

            Thank you for your registration.

            If you have any questions or need further assistance, please don't hesitate to contact our support team.

            Best regards,
            Collegecue
            Support Team
            '''
            email = EmailMessage(subject, message, sender_email, recipient_email)
            # email.content_subtype = "html"
            email.send()
            return JsonResponse({'success': True, 'message': 'Registration successful'})
        else:
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)


@csrf_exempt
def register_job_seeker(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON'}, status=400)

        form = JobSeekerRegistrationForm(data)
        if form.is_valid():
            job_seeker = form.save(commit=False)
            job_seeker.password = make_password(form.cleaned_data['password'])
            job_seeker.save()

            sender_email = settings.EMAIL_HOST_USER
            recipient_email = [job_seeker.email]
            subject = 'Confirmation Mail'
            message = '''Dear User,

            Thank you for your registration.

            If you have any questions or need further assistance, please don't hesitate to contact our support team.

            Best regards,
            Collegecue
            Support Team
            '''
            email = EmailMessage(subject, message, sender_email, recipient_email)
            email.send()

            return JsonResponse({'success': True, 'message': 'Registration successful'}, status=201)

        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({'success': False, 'errors': 'Only POST requests are allowed.'}, status=405)


@csrf_protect
def search(request):
    api_key = 'f120cebcf2a4379d72b80691ed4fe25bfc7443b11ce3739e6ee7e1bb790923505b48f76881878ee5f8f6af795bfc2c0be5c7d130dc820f3503bf58cced23e7c8462c10cf656a865164d8a6546f14a10f9c0bd31ed348f8774e6b47cb930a6266e13479cbf80f0a6e6c888e2c01696a0cd94b0b6d2da1dbc9eebc862985cdf64b'
    query = request.GET.get('q', '').lower()
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    headers = {'Authorization': f'Bearer {api_key}'}

    apis = {
        'http://195.35.22.140:1337/api/abroad-exams': '/abroad-exam/{id}',
        'http://195.35.22.140:1337/api/bank-loans': '/bank-loan/{id}',
        'http://195.35.22.140:1337/api/do-and-donts': '/do-and-dont/{id}',
        'http://195.35.22.140:1337/api/exam-categories': '/exam-category/{id}',
        'http://195.35.22.140:1337/api/faqs': '/faq/{id}',
        'http://195.35.22.140:1337/api/general-instructions': '/general-instruction/{id}',
        'http://195.35.22.140:1337/api/instructions-and-navigations': '/instruction-and-navigation/{id}',
        'http://195.35.22.140:1337/api/practice-questions': '/practice-question/{id}',
        'http://195.35.22.140:1337/api/q-and-as': '/q-and-a/{id}',
        'http://195.35.22.140:1337/api/rules': '/rule/{id}',
        'http://195.35.22.140:1337/api/test-series-faqs': '/test-series-faq/{id}',
        'http://195.35.22.140:1337/api/college-infos?populate=*': '/college/{id}'
    }

    combined_result = []

    for api, path_template in apis.items():
        try:
            response = requests.get(api, headers=headers, timeout=9000)
            response.raise_for_status()
            api_data = response.json().get('data', [])
            for item in api_data:
                item['path'] = path_template.format(id=item['id'])
                combined_result.append(item)
        except requests.RequestException as e:
            return JsonResponse({'error': f'Error fetching API {api}: {e}'}, status=500)

    matching_objects = [data for data in combined_result if query in json.dumps(data).lower()]

    paginator = Paginator(matching_objects, per_page)
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    paginated_response = {
        'total_results': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': results.number,
        'results': results.object_list
    }

    return JsonResponse(paginated_response, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class Subscriber_view(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            form = SubscriptionForm(data)
            if form.is_valid():
                subscriber = form.save()
                if subscriber.email and subscriber.subscribed_at:
                    return JsonResponse({'message': f'You have successfully subscribed at {subscriber.subscribed_at}'})
                return JsonResponse({'error': 'Please subscribe'}, status=400)
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class Subscriber_view1(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            form = SubscriptionForm1(data)
            if form.is_valid():
                subscriber = form.save()
                if subscriber.email and subscriber.subscribed_at:
                    return JsonResponse({'message': f'You have successfully subscribed at {subscriber.subscribed_at}'})
                return JsonResponse({'error': 'Please subscribe'}, status=400)
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LoginCompanyInChargeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            email, password = data.get('official_email'), data.get('password')

            company = CompanyInCharge.objects.filter(official_email=email).first()
            if not company:
                return JsonResponse({'error': 'Company not found'}, status=404)

            if check_password(password, company.password):
                token = generate_unique_token()
                company.token = token
                company.save()

                send_mail(
                    subject='Login Successful',
                    message=f'Hello {company.official_email},\n\nYou have successfully logged in.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[company.official_email],
                    fail_silently=False,
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Login successful for {company.official_email}',
                    'token': token,
                    'official_email':company.official_email,
                    'id':company.id,
                    'phone':company.mobile_number,
                    'company_name':company.company_name,
                    'model':'CompanyInCharge'
                    
                }, status=200)

            return JsonResponse({'error': 'Invalid credentials'}, status=400)

        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid JSON or missing fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LoginUniversityInChargeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            email, password = data.get('official_email'), data.get('password')

            university = UniversityInCharge.objects.filter(official_email=email).first()
            if not university:
                return JsonResponse({'error': 'University not found'}, status=404)

            if check_password(password, university.password):
                token = generate_unique_token()
                university.token = token
                university.save()

                send_mail(
                    subject='Login Successful',
                    message=f'Hello {university.official_email},\n\nYou have successfully logged in.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[university.official_email],
                    fail_silently=False,
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Login successful for {university.official_email}',
                    'token': token,
                    'collegeid':university.id,
                    'official_email':university.official_email,
                    'university_name':university.university_name,
                    'phone':university.mobile_number,
                    'model':'UniversityInCharge',
                }, status=200)

            return JsonResponse({'error': 'Invalid credentials'}, status=400)

        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid JSON or missing fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LoginConsultantView(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            email, password = data.get('official_email'), data.get('password')

            consultant = Consultant.objects.filter(official_email=email).first()
            if not consultant:
                return JsonResponse({'error': 'Consultant not found'}, status=404)

            if check_password(password, consultant.password):
                token = generate_unique_token()
                consultant.token = token
                consultant.save()

                send_mail(
                    subject='Login Successful',
                    message=f'Hello {consultant.official_email},\n\nYou have successfully logged in.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[consultant.official_email],
                    fail_silently=False,
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Login successful for {consultant.official_email}',
                    'token': token
                }, status=200)

            return JsonResponse({'error': 'Invalid credentials'}, status=400)

        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid JSON or missing fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

##def verify_token(request):
##    try:
##        token = request.POST.get('idtoken')    # Frontend provides this token
##        if not token:
##            return JsonResponse({'error': 'Token missing'}, status=400)
##
##        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
##        if idinfo.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
##            return JsonResponse({'error': 'Wrong issuer.'}, status=400)
##
##        return JsonResponse({'email': idinfo.get('email')})
##
##    except ValueError as ve:
##        return JsonResponse({'error': str(ve)}, status=400)
##    except Exception as e:
##        return JsonResponse({'error': str(e)}, status=500)
##
##def verify_linkedin_token(request):
##    token = request.POST.get('idtoken')  # Frontend provides this token
##    if not token:
##        return JsonResponse({'error': 'Token missing'}, status=400)
##
##    try:
##        verify_url = 'https://api.linkedin.com/v2/me'
##        headers = {'Authorization': f'Bearer {token}'}
##
##        response = requests.get(verify_url, headers=headers, timeout=9000)
##
##        if response.status_code == 200:
##            user_info = response.json()
##            return JsonResponse({
##                'id': user_info.get('id'),
##                'email': user_info.get('emailAddress')
##            })
##
##        return JsonResponse({'error': 'Invalid token'}, status=400)
##
##    except Exception as e:
##        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutCompanyInChargeView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to logout'}, status=400)

            company = CompanyInCharge.objects.filter(token=token).first()
            if not company:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            company.token = None
            company.save()

            return JsonResponse({'success': True, 'message': 'Logout successful'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutUniversityView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to logout'}, status=400)

            university = UniversityInCharge.objects.filter(token=token).first()
            if not university:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            university.token = None
            university.save()

            return JsonResponse({'success': True, 'message': 'Logout successful'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutConsultantView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to logout'}, status=400)

            consultant = Consultant.objects.filter(token=token).first()
            if not consultant:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            consultant.token = None
            consultant.save()

            return JsonResponse({'success': True, 'message': 'Logout successful'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def login_job_seeker(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Please provide both email and password'}, status=400)

            job_seeker = JobSeeker.objects.filter(email=email).first()

            if not job_seeker or not check_password(password, job_seeker.password):
                return JsonResponse({'error': 'Invalid email or password'}, status=400)

            job_seeker.token = generate_unique_token()
            job_seeker.save()

            return JsonResponse({'message': 'Login successful', 
                                 'unique_token': job_seeker.token, 
                                 'userid':job_seeker.id, 
                                 'useremail':job_seeker.email,
                                 'first_name':job_seeker.first_name,
                                 'last_number':job_seeker.last_name,
                                 'phone':job_seeker.mobile_number,
                                 'model':'JobSeeker',
                                 }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'errors': 'Only POST requests are allowed.'}, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class JobSeekerLogoutView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to logout'}, status=400)

            job_seeker = JobSeeker.objects.filter(token=token).first()
            if not job_seeker:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            job_seeker.token = None
            job_seeker.save()

            return JsonResponse({'success': True, 'message': 'Logout successful'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordJobSeekerView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            token = auth_header.split(' ')[1]

            data = json.loads(request.body.decode('utf-8'))
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            official_email = data.get('official_email')
            old_password = data.get('old_password')

            if not all([official_email, old_password, new_password, confirm_password]):
                return JsonResponse({'error': 'All fields are required'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)

            job_seeker = JobSeeker.objects.filter(email=official_email, token=token).first()
            if not job_seeker:
                return JsonResponse({'error': 'Job seeker not found or invalid token'}, status=404)

            if not check_password(old_password, job_seeker.password):
                return JsonResponse({'error': 'Old password is incorrect'}, status=400)
            
            job_seeker.password = make_password(new_password)
            job_seeker.save()

            return JsonResponse({'success': True, 'message': 'Password has been changed successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordCompanyInChargeView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            token = auth_header.split(' ')[1]

            data = json.loads(request.body.decode('utf-8'))
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            if not new_password or not confirm_password:
                return JsonResponse({'error': 'New password and confirmation are required'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)

            official_email = data.get('official_email')
            if not official_email:
                return JsonResponse({'error': 'Official email is required'}, status=400)

            company = CompanyInCharge.objects.filter(official_email=official_email, token=token).first()
            if not company:
                return JsonResponse({'error': 'Company not found or invalid token'}, status=404)

            old_password = data.get('old_password')
            if not check_password(old_password, company.password):
                return JsonResponse({'error': 'Old password is incorrect'}, status=400)

            company.password = make_password(new_password)
            company.save()

            return JsonResponse({'success': True, 'message': 'Password has been changed successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordUniversityInChargeView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            token = auth_header.split(' ')[1]

            data = json.loads(request.body.decode('utf-8'))
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            if not new_password or not confirm_password:
                return JsonResponse({'error': 'New password and confirmation are required'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)

            university = UniversityInCharge.objects.filter(token=token).first()
            if not university:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            university.password = make_password(new_password)
            university.save()
            return JsonResponse({'success': True, 'message': 'Password changed successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordConsultantView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)
            
            token = auth_header.split(' ')[1]

            data = json.loads(request.body.decode('utf-8'))
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            if not new_password or not confirm_password:
                return JsonResponse({'error': 'New password and confirmation are required'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)
            
            consultant = Consultant.objects.filter(token=token).first()
            if not consultant:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            consultant.password = make_password(new_password)
            consultant.save()
            return JsonResponse({'success': True, 'message': 'Password changed successfully'}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteCompanyInChargeAccountView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            token = auth_header.split(' ')[1]

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to delete account'}, status=400)

            company = CompanyInCharge.objects.filter(token=token).first()
            if not company:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            company.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteJobSeekerAccountView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            token = auth_header.split(' ')[1]
            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to delete account'}, status=400)

            job_seeker = JobSeeker.objects.filter(token=token).first()
            if not job_seeker:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            job_seeker.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteUniversityAccountView(View):
    def post(self, request):
        try:
            token = request.headers.get('Authorization', '').split(' ')[1]
            data = json.loads(request.body.decode('utf-8'))

            if not token or not data.get('confirmation'):
                return JsonResponse({'error': 'Token or confirmation missing'}, status=400)

            university = UniversityInCharge.objects.filter(token=token).first()
            if not university:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            university.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or missing token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteConsultantAccountView(View):
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

            if not token:
                return JsonResponse({'error': 'Token is missing or invalid format'}, status=400)

            data = json.loads(request.body.decode('utf-8'))
            if not data.get('confirmation', False):
                return JsonResponse({'error': 'Confirmation is required to delete account'}, status=400)

            consultant = Consultant.objects.filter(token=token).first()
            if not consultant:
                return JsonResponse({'error': 'Invalid token'}, status=404)

            consultant.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'}, status=200)

        except (json.JSONDecodeError, IndexError):
            return JsonResponse({'error': 'Invalid JSON or token'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

#K