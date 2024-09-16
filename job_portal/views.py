from django.db import IntegrityError, OperationalError
from django.shortcuts import get_object_or_404 # type: ignore
from django.http import JsonResponse # type: ignore
from django.middleware.csrf import get_token # type: ignore
from django.views.decorators.csrf import csrf_exempt, csrf_protect # type: ignore
from django.utils import timezone # type: ignore
from django.db.models import Q,Subquery, OuterRef # type: ignore
from rest_framework.response import Response # type: ignore
from .models import CandidateStatus_rejected, CandidateStatus_under_review, Job, Application, Company,CandidateStatus_selected,CandidateStatus_not_eligible, Resume, Student, User,Message,Attachment
from .forms import AchievementForm, CertificationForm, CompanyForm, EducationForm, ExperienceForm, JobForm, ApplicationForm, ObjectiveForm, ProjectForm, PublicationForm, ReferenceForm, ResumeForm, StudentForm
import json, operator
from datetime import timedelta
from django.utils.decorators import method_decorator # type: ignore
from django.views import View # type: ignore
from rest_framework.authtoken.views import ObtainAuthToken # type: ignore
from rest_framework.authtoken.models import Token # type: ignore
from rest_framework import status # type: ignore
from functools import reduce
from django.core.exceptions import ObjectDoesNotExist

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

@csrf_protect
def job_list(request):
    try:
        if request.method == 'GET':
            filter_params = {
                'search_query': request.GET.get('search', ''),
                'job_title': request.GET.get('job_title', ''),
                'sort_order': request.GET.get('sort', ''),
                'job_type': request.GET.get('job_type', ''),
                'company_name': request.GET.get('company', ''),
                'experience_level': request.GET.get('experience', ''),
                'explore_new_jobs': request.GET.get('explore_new_jobs', ''),
                'category': request.GET.get('category', ''),
                'skills': request.GET.get('skills', ''),
                'workplaceTypes': request.GET.get('workplaceTypes', '')
            }

            jobs = Job.objects.all()
            filters = []

            if filter_params['search_query']:
                filters.append(Q(job_title__icontains=filter_params['search_query']))
            if filter_params['company_name']:
                filters.append(Q(company__icontains=filter_params['company_name']))
            if filter_params['job_title']:
                filters.append(Q(job_title__icontains=filter_params['job_title']))
            if filter_params['job_type']:
                filters.append(Q(job_type__icontains=filter_params['job_type']))
            if filter_params['experience_level']:
                filters.append(Q(experience__icontains=filter_params['experience_level']))
            if filter_params['category']:
                filters.append(Q(category__icontains=filter_params['category']))
            if filter_params['workplaceTypes']:
                filters.append(Q(workplaceTypes__icontains=filter_params['workplaceTypes']))

            if filter_params['skills']:
                skills_list = filter_params['skills'].split(',')
                for skill in skills_list:
                    filters.append(Q(skills__icontains=skill))

            if filters:
                jobs = jobs.filter(reduce(operator.and_, filters))

            if filter_params['explore_new_jobs']:
                days = 7 if filter_params['explore_new_jobs'] == 'week' else 30
                start_date = timezone.now() - timedelta(days=days)
                jobs = jobs.filter(published_at__gte=start_date)

            if filter_params['sort_order']:
                jobs = jobs.order_by(filter_params['sort_order'])

            jobs_list = [{
                'id': job.id,
                'job_title': job.job_title,
                'company': job.company,
                'location': job.location,
                'requirements': job.requirements,
                'job_type': job.job_type,
                'experience': job.experience,
                'category': job.category,
                'published_at': job.published_at,
                'skills': job.skills,
                'workplaceTypes': job.workplaceTypes,
                'questions': job.questions,
            } for job in jobs]

            return JsonResponse(jobs_list, safe=False, status=200)

        elif request.method == 'POST':
            return handle_post_request(request)

        return JsonResponse({'error': 'Method not allowed'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
  
@csrf_exempt
def handle_post_request(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if Job.objects.filter(company=data['company']).count() >= 100:
        return JsonResponse({'message': 'Limit exceeded for job postings by this company'}, status=200)

    job_skills = data.get('skills', '')
    if job_skills:
        unique_job_list = list(set(job_skills.split(', ')))
        data['skills'] = ', '.join(unique_job_list)

    form = JobForm(data)
    if form.is_valid():
        job = form.save()
        return JsonResponse({'message': 'Job created successfully', 'job_id': job.id}, status=201)

    return JsonResponse({'errors': form.errors}, status=400)

@csrf_protect
def job_detail(request, job_id):
    try:
        job = get_object_or_404(Job, id=job_id)
        if request.method == 'GET':
            return JsonResponse({
                'id': job.id,
                'title': job.job_title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'requirements': job.requirements,
                'job_type': job.job_type,
                'experience': job.experience,
                'category': job.category,
                'published_at': job.published_at
            })

        elif request.method == 'PUT':
            data = json.loads(request.body)
            form = JobForm(data, instance=job)
            if form.is_valid():
                form.save()
                return JsonResponse({'message': 'Job updated successfully'}, status=200)
            return JsonResponse({'errors': form.errors}, status=400)

        elif request.method == 'DELETE':
            job.delete()
            return JsonResponse({'message': 'Job deleted successfully'}, status=200)
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def apply_job(request, job_id):
    try:
        json_data = json.loads(request.POST.get('data'))
        job = get_object_or_404(Job, id=job_id)
        if request.method == 'POST':
            form = ApplicationForm(json_data, request.FILES)
            if form.is_valid():
                application = form.save(commit=False)
                application.job = job
                job_skills = set(job.skills.split(', '))
                candidate_skills = set(application.skills.split(', '))
                cand_skills = ', '.join(candidate_skills)
                application.skills = cand_skills

                if not job_skills.intersection(candidate_skills):
                    return JsonResponse({'message': 'Candidate is not eligible to apply'}, status=404)

                application.save()
                return JsonResponse({'message': 'Application submitted successfully', 'application_id': application.id}, status=201)
            return JsonResponse({'errors': form.errors}, status=400)
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_protect
def job_applications(request, job_id):
    try:
        job = get_object_or_404(Job, id=job_id)
        applications = Application.objects.filter(job=job)
        applications_list = [{
            'id': app.id,
            'candidate_name': app.candidate_name,
            'email': app.email,
            'phone_number': app.phone_number,
            'resume_url': app.resume.url if app.resume else '',
            'cover_letter': app.cover_letter,
            'status': app.status,
            'applied_at': app.applied_at,
        } for app in applications]
        return JsonResponse(applications_list, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def job_status(request, job_id):
    try:
        pending_applications = Application.objects.filter(job_id=job_id, status='pending')
        pending_count = pending_applications.count()

        return JsonResponse({
            'job_id': job_id,
            'pending_count': pending_count
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CompanyListCreateView(View):
    def get(self, request):
        try:
            companies = list(Company.objects.all().values())
            return JsonResponse(companies, safe=False, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def post(self, request):
        try:
            data = json.loads(request.body)
            form = CompanyForm(data)
            if form.is_valid():
                form.save()
                return JsonResponse({'message': 'Company Created Successfully'}, status=201)
            else:
                return JsonResponse(form.errors, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CompanyDetailView(View):
    def get(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
            return JsonResponse({
                "id": company.id,
                "name": company.name,
                "address": company.address,
                "city": company.city,
                "state": company.state,
                "country": company.country_name,
                "website": company.website
            })
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def put(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
            data = json.loads(request.body)
            form = CompanyForm(data, instance=company)
            if form.is_valid():
                company = form.save()
                return JsonResponse({'message': 'Company Updated successfully'}, status=200)
            else:
                return JsonResponse(form.errors, status=400)
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Company not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
            company.delete()
            return JsonResponse({'message': 'Company deleted successfully'}, status=200)
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def find_status(request):
    try:
        co_name = request.GET['name']
        job_ids = Job.objects.filter(company=co_name)
        applications = Application.objects.filter(job__in=job_ids)
        statuses = {}
        for application in applications:
            if application.status not in statuses:
                statuses[application.status] = 1
            else:
                statuses[application.status] += 1
        return JsonResponse({'message': statuses}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def candidate_profile(request):
    try:
        json_data = json.loads(request.POST.get('data'))
        skills_can = json_data['skills']
        can_skills_set = set(skills_can.split(', '))
        skills_of_can = ', '.join(can_skills_set)
        print(skills_of_can)
        can_location = json_data['location']
        experience_year = json_data['experience_years']
        print(experience_year)
        matching_jobs = []
        all_jobs = Job.objects.all()
        for job in all_jobs:
            job_skills_set = set(job.skills.split(', '))
            ex_year_arr = job.experience_yr.split('-')
            print(ex_year_arr)
            if can_skills_set.intersection(job_skills_set) and experience_year >= int(ex_year_arr[0]) and experience_year <= int(ex_year_arr[1]) and job.location == can_location:
                matching_jobs.append({
                    "id": job.id,
                    "title": job.job_title,
                    "company": job.company,
                    "experience_year": job.experience_yr,
                    "location": job.location,
                })

        return JsonResponse({'matching_jobs': matching_jobs})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def company_status(request, status_choice):
    try:
        co_name = request.GET['name']
        job_id = Job.objects.filter(company=co_name)
        apply_id = Application.objects.filter(job__in=job_id)
        name = []
        if status_choice == 'selected':
            candidate_status_modelname = CandidateStatus_selected
        elif status_choice == 'rejected':
            candidate_status_modelname = CandidateStatus_rejected
        elif status_choice == 'not_eligible':
            candidate_status_modelname = CandidateStatus_not_eligible
        elif status_choice == 'under_review':
            candidate_status_modelname = CandidateStatus_under_review
        for application in apply_id:
            if application.status == status_choice:
                name.append(application.candidate_name)
                candidate_status_modelname.objects.create(
                    candidate_name=application.candidate_name,
                    status=status_choice,
                    company_name=co_name,
                    job_id=application.job_id
                )

        return JsonResponse({'message': name}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def create_resume(request):
    if request.method == 'POST':
        try:
            resume_form = ResumeForm(request.POST, request.FILES)

            if resume_form.is_valid():
                resume = resume_form.save()

                objective_data = request.POST.get('objective', {})
                if objective_data:
                    objective_form = ObjectiveForm(json.loads(objective_data))
                    if objective_form.is_valid():
                        objective = objective_form.save(commit=False)
                        objective.resume = resume
                        objective.save()

                education_data = json.loads(request.POST.get('education', '[]'))
                for item in education_data:
                    education_form = EducationForm(item)
                    if education_form.is_valid():
                        education = education_form.save(commit=False)
                        education.resume = resume
                        education.save()

                experience_data = json.loads(request.POST.get('experience', '[]'))
                for item in experience_data:
                    experience_form = ExperienceForm(item)
                    if experience_form.is_valid():
                        experience = experience_form.save(commit=False)
                        experience.resume = resume
                        experience.save()

                project_data = json.loads(request.POST.get('projects', '[]'))
                for item in project_data:
                    project_form = ProjectForm(item)
                    if project_form.is_valid():
                        project = project_form.save(commit=False)
                        project.resume = resume
                        project.save()

                reference_data = json.loads(request.POST.get('references', '[]'))
                for item in reference_data:
                    reference_form = ReferenceForm(item)
                    if reference_form.is_valid():
                        reference = reference_form.save(commit=False)
                        reference.resume = resume
                        reference.save()

                certifications_data = json.loads(request.POST.get('certifications', '[]'))
                for item in certifications_data:
                    certifications_form = CertificationForm(item)
                    if certifications_form.is_valid():
                        certifications = certifications_form.save(commit=False)
                        certifications.resume = resume
                        certifications.save()

                achievements_data = json.loads(request.POST.get('achievements', '[]'))
                for item in achievements_data:
                    achievements_form = AchievementForm(item)
                    if achievements_form.is_valid():
                        achievements = achievements_form.save(commit=False)
                        achievements.resume = resume
                        achievements.save()

                publications_data = json.loads(request.POST.get('publications', '[]'))
                for item in publications_data:
                    publications_form = PublicationForm(item)
                    if publications_form.is_valid():
                        publications = publications_form.save(commit=False)
                        publications.resume = resume
                        publications.save()

                return JsonResponse({'status': 'success', 'resume_id': resume.id})

            return JsonResponse({'status': 'error', 'errors': resume_form.errors})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        except IntegrityError:
            return JsonResponse({'status': 'error', 'message': 'Database integrity error'}, status=500)

        except OperationalError:
            return JsonResponse({'status': 'error', 'message': 'Database operational error'}, status=500)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def get_resume_detail_by_id(request, resume_id):
    try:
        if request.method == 'GET':
            resume = get_object_or_404(Resume, id=resume_id)

            resume_data = {
                "first_name": resume.first_name,
                "last_name":resume.last_name,
                "email": resume.email,
                "phone": resume.phone,
                "address": resume.address,
                "date_of_birth": resume.date_of_birth,
                "website_urls": resume.website_urls,
                "skills": resume.skills,
                "activities": resume.activities,
                "interests": resume.interests,
                "languages": resume.languages,
                "bio": resume.bio,
                "city": resume.city,
                "state": resume.state,
                "country": resume.country,
                "zipcode": resume.zipcode,
                # "attachments": resume.Attachment,
                "objective": resume.objective.text if hasattr(resume, 'objective') else 'Not specified',
                "education": [
                    {
                        "course_or_degree": education.course_or_degree,
                        "school_or_university": education.school_or_university,
                        "grade_or_cgpa": education.grade_or_cgpa,
                        "start_date": education.start_date,
                        "end_date": education.end_date,
                    } for education in resume.education_entries.all()
                ],
                "experience": [
                    {
                        "job_title": experience.job_title,
                        "company_name": experience.company_name,
                        "start_date": experience.start_date,
                        "end_date": experience.end_date,
                        "description": experience.description,
                    } for experience in resume.experience_entries.all()
                ],
                "projects": [
                    {
                        "title": project.title,
                        "description": project.description,
                    } for project in resume.projects.all()
                ],
                "references": [
                    {
                        "name": reference.name,
                        "contact_info": reference.contact_info,
                        "relationship": reference.relationship,
                    } for reference in resume.references.all()
                ],
                "certifications": [
                    {
                        "name": certification.name,
                        "start_date": certification.start_date,
                        "end_date": certification.end_date, 
                    } for certification in resume.certifications.all()
                ],
                "achievements": [
                    {
                        "title": achievement.title,
                        "publisher": achievement.publisher,
                        "date_of_issue": achievement.date_of_issue,
                    } for achievement in resume.achievements.all()
                ],
                "publications": [
                    {
                        "title": publication.title,
                        "publisher": publication.publisher,
                        "date_of_publication": publication.date_of_publications,
                    } for publication in resume.publications.all()
                ]
            }
            
            return JsonResponse(resume_data, status=200)
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def count_jobs_by_category(request):
    if request.method == 'GET':
        try:
            category_counts = {}

            jobs = Job.objects.all()

            for job in jobs:
                category = job.category.strip()
                if category and category in category_counts:
                    category_counts[category] += 1
                elif category:
                    category_counts[category] = 1

            response_data = [
                {'category': category, 'job_count': count}
                for category, count in category_counts.items()
            ]

            return JsonResponse({'category_counts': response_data}, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)
                message = "New token created" if created else "Existing token retrieved"
                return Response({
                    'token': token.key,
                    'username': user.username,
                    'message': message
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def fetch_jobs_by_exp_skills(request):
    try:
        if request.method == 'GET':
            experience = request.GET.get('experience')
            skills = request.GET.get('skills')

            skills_list = [skill.strip().lower() for skill in skills.split(',')] if skills else []

            jobs = Job.objects.all()

            if experience:
                jobs = jobs.filter(experience=experience)
            if skills_list:
                queries = Q()
                for skill in skills_list:
                    queries |= Q(skills__icontains=skill)
                jobs = jobs.filter(queries).distinct()

            if not (experience or skills_list):
                return JsonResponse({'error': 'Please enter at least one filter: experience or skills.'}, status=400)

            job_list = []
            for job in jobs:
                job_list.append({
                    'job_title': job.job_title,
                    'company_name': job.company,
                    'location': job.location,
                    'workplaceType': job.workplaceTypes,
                    'description': job.description,
                    'requirements': job.requirements,
                    'job_type': job.job_type,
                    'experience': job.experience,
                    'category': job.category,
                    'required_skills': job.skills,
                    'experience_yr': job.experience_yr,
                })

            return JsonResponse({'jobs': job_list}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def fetch_jobs_by_category_location_skills(request):
    try:
        if request.method == 'GET':
            category = request.GET.get('category')
            location = request.GET.get('location')
            skills = request.GET.get('skills')

            skills_list = [skill.strip().lower() for skill in skills.split(',')] if skills else []

            jobs = Job.objects.all()

            if category:
                jobs = jobs.filter(category=category)
            if location:
                jobs = jobs.filter(location=location)
            if skills_list:
                queries = Q()
                for skill in skills_list:
                    queries |= Q(skills__icontains=skill)
                jobs = jobs.filter(queries).distinct()

            if not (category or location or skills_list):
                return JsonResponse({'error': 'Please enter at least one filter: category, location or skills.'}, status=400)

            job_list = []
            for job in jobs:
                job_list.append({
                    'job_title': job.job_title,
                    'company_name': job.company,
                    'location': job.location,
                    'workplaceType': job.workplaceTypes,
                    'description': job.description,
                    'requirements': job.requirements,
                    'job_type': job.job_type,
                    'experience': job.experience,
                    'category': job.category,
                    'required_skills': job.skills,
                    'experience_yr': job.experience_yr,
                })

            return JsonResponse({'jobs': job_list}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_titles(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            job_title = {
                job.job_title: job.job_title
                for job in jobs
                if job.job_title
            }
            return JsonResponse({'job_title': job_title})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_types(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            job_types = {
                job.job_type: job.job_type
                for job in jobs
                if job.job_type
            }
            return JsonResponse({'job_types': job_types})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_experience(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            exp_types = {
                job.experience: job.experience
                for job in jobs
                if job.experience
            }
            return JsonResponse({'exp_types': exp_types})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_category(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            category = {
                job.category: job.category
                for job in jobs
                if job.category
            }
            return JsonResponse({'category': category})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_workplaceTypes(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            workplaceTypes = {
                job.workplaceTypes: job.workplaceTypes
                for job in jobs
                if job.workplaceTypes
            }
            return JsonResponse({'workplaceTypes': workplaceTypes})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_job_location(request):
    try:
        if request.method == 'GET':
            jobs = Job.objects.all()

            location = {
                job.location: job.location
                for job in jobs
                if job.location
            }
            return JsonResponse({'location': location})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_sector_types(request):
    try:
        if request.method == 'GET':
            companies = Company.objects.all()

            sector_types = {
                company.sector_type: company.sector_type
                for company in companies
                if company.sector_type
            }
            return JsonResponse({'sector_type': sector_types})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_country_types(request):
    try:
        if request.method == 'GET':
            companies = Company.objects.all()

            country_name = {
                company.country_name: company.country_name
                for company in companies
                if company.country_name
            }
            return JsonResponse({'country_name': country_name})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def fetch_status_choices(request):
    try:
        if request.method == 'GET':
            applications = Application.objects.all()

            status = {
                application.status: application.status
                for application in applications
                if application.status
            }
            return JsonResponse({'status': status})
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def application_status_counts(request):
    try:
        email = request.GET.get('email')
        if not email:
            return JsonResponse({'error': 'Email parameter is required'}, status=400)

        pending_count = Application.objects.filter(email=email, status='pending').count()
        interview_scheduled_count = Application.objects.filter(email=email, status='interview_scheduled').count()
        rejected_count = Application.objects.filter(email=email, status='rejected').count()

        return JsonResponse({
            'pending_count': pending_count,
            'interview_scheduled': interview_scheduled_count,
            'rejected_count': rejected_count
        })

    except Application.DoesNotExist:
        return JsonResponse({'error': 'No applications found for the provided email.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred', 'details': str(e)}, status=500)

def filter_applied_jobs(request):
    try:
        email = request.GET.get('email')
        if not email:
            return JsonResponse({'error': 'Email parameter is required'}, status=400)

        job_title = request.GET.get('job_title')
        status = request.GET.get('status')
        job_type = request.GET.get('job_type')
        sort_by = request.GET.get('sort_by')  

        applications = Application.objects.filter(email=email)
        
        if job_title:
            applications = applications.filter(job__job_title=job_title) 
            
        if status:
            applications = applications.filter(status=status)
            
        if job_type:
            applications = applications.filter(job__job_type=job_type)

        if sort_by == 'job_title_asc':
            applications = applications.order_by('job__job_title')  
        elif sort_by == 'job_title_desc':
            applications = applications.order_by('-job__job_title')  
        elif sort_by == 'applied_at_asc':
            applications = applications.order_by('applied_at')  
        elif sort_by == 'applied_at_desc':
            applications = applications.order_by('-applied_at')  

        result = []
        for application in applications:
            result.append({
                'job_title': application.job.job_title,
                'company': application.job.company,
                'job_location': application.job.location,
                'job_type': application.job.job_type,
                'status': application.status,
                'applied_at': application.applied_at,
            })

        return JsonResponse(result, safe=False)

    except Application.DoesNotExist:
        return JsonResponse({'error': 'No applications found for the provided email'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
      
def sort_saved_jobs(request):
    try:
        job_type = request.GET.get('job_type')
        category = request.GET.get('category')

        jobs = Job.objects.all()

        if job_type:
            jobs = jobs.filter(job_type=job_type)

        if category:
            jobs = jobs.filter(category=category)
            
        if not (job_type or category):
            return JsonResponse({'error': 'Please select at least one filter: job_type or category'}, status=400)

        jobs_list = [{
            'id': job.id,
            'job_title': job.job_title,
            'company': job.company,
            'location': job.location,
            'requirements': job.requirements,
            'job_type': job.job_type,
            'experience': job.experience,
            'category': job.category,
            'published_at': job.published_at,
            'skills': job.skills,
            'workplaceTypes': job.workplaceTypes,
        } for job in jobs]

        return JsonResponse({'saved_jobs': jobs_list}, safe=False)

    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'User is not authenticated'}, status=403)

        confirm = request.POST.get('confirm')
        if confirm is None:
            return JsonResponse({'status': 'error', 'message': 'Confirm parameter is missing'}, status=400)

        if confirm == 'yes':
            request.user.delete()
            return JsonResponse({'status': 'success', 'message': 'Account deleted successfully'}, status=200)
        elif confirm == 'no':
            return JsonResponse({'status': 'canceled', 'message': 'Account deletion canceled'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid confirm value'}, status=400)

   
@csrf_exempt
def myInbox(request):
    if(request.method=="POST"):
        try:
            data = json.loads(request.body)
            email = data['email']
            filter = data['filter']

            last_message_subquery = Message.objects.filter(
                Q(sender__email=OuterRef('email'), recipient__email=email) |
                Q(recipient__email=OuterRef('email'), sender__email=email)
            ).order_by('-id').values_list('id', flat=True)[:1]


            user_subquery = User.objects.filter(
                Q(sender__recipient__email=email) | Q(recipient__sender__email=email)
            ).annotate(
                last_msg=Subquery(last_message_subquery)
            ).values_list('last_msg', flat=True).order_by('-id')

            messages_query = Message.objects.filter(
                id__in=Subquery(user_subquery)
            ).order_by('-id')

            if filter == 'read':
                messages_query = messages_query.filter(is_read=True)
            elif filter == 'unread':
                messages_query = messages_query.filter(is_read=False)
            elif filter =='primary':
                messages_query = messages_query.filter(is_primary=True)
            
            message_list = []
            for message in messages_query:

                attachments = message.attachments.all()

                attachment_list = [{
                    'id': attachment.id,
                    'file_url': attachment.file.url,
                    'uploaded_at': attachment.uploaded_at
                } for attachment in attachments]

                message_list.append({
                    'id': message.id,
                    'sender': message.sender.email,
                    'recipient': message.recipient.email,
                    'content': message.content,
                    'timestamp': message.timestamp,
                    'is_read': message.is_read,
                    'attachments': attachment_list
                })

            return JsonResponse({
                'status': 'success',
                'messages': message_list
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                'status': 'false',
                'error': str(e)
            }, status=500)


@csrf_exempt
def getMessages(request):
    if request.method=="POST":
        data = json.loads(request.body)
        sender_email = data['sender_email']
        recipient_email = data['recipient_email']

        sender = User.objects.get(email=sender_email)
        recipient = User.objects.get(email=recipient_email)

        messages = Message.objects.filter(
            Q(sender=sender, recipient=recipient) |
            Q(sender=recipient, recipient=sender)
        ).order_by('timestamp')

        Message.objects.filter(
            sender=sender,
            recipient=recipient,
            is_read=False
        ).update(is_read=True)

        message_list = []
        for message in messages:
            attachments = message.attachments.all()

            attachment_list = [{
                'id': attachment.id,
                'file_url': attachment.file.url,
                'uploaded_at': attachment.uploaded_at
            } for attachment in attachments]

            message_list.append({
                'id': message.id,
                'sender': message.sender.email,
                'recipient': message.recipient.email,
                'content': message.content,
                'timestamp': message.timestamp,
                'is_read': message.is_read,
                'attachments': attachment_list
            })


        return JsonResponse({
            'status': 'success',
            'messages': message_list
        }, status=200)


@csrf_exempt
def sendMessage(request):
    if request.method == "POST":
        try:
            sender_email = request.POST['sender_email']
            recipient_email = request.POST['recipient_email']
            message_content = request.POST['content']

            sender = get_object_or_404(User,email=sender_email)
            recipient = get_object_or_404(User,email=recipient_email)
            
            if message_content=="":
                return JsonResponse({'status': 'false', 'message': 'Message is empty'}, status=401)
            
            message = Message.objects.create(sender=sender,recipient=recipient,
            content=message_content)

            if request.FILES:
                for file in request.FILES.getlist('attachments'):
                    Attachment.objects.create(message=message, file=file)

            return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'}, status=201)

        except KeyError:
            return JsonResponse({'status': 'error', 'message': 'Invalid request. Missing fields.'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def searchUser(request):
    if request.method=="GET":
        query = request.GET.get('q', '').strip()
        if query:
            contacts = User.objects.filter(
                Q(firstname__icontains=query) |
                Q(lastname__icontains=query)
            )

            contact_list = list(contacts.values())
            print(contact_list)

            return JsonResponse({
            'status': 'success',
            'contacts': contact_list
            }, status=200)
        
        else:
            contacts = User.objects.all().values('id', 'firstname','lastname','email')
            contact_list = list(contacts)

            return JsonResponse({
                'status': 'success',
                'contacts': contact_list
            }, status=200)
            
@csrf_exempt
def save_student(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = StudentForm(data)
        if form.is_valid():
            form.save()  
            return JsonResponse({'message': 'Student data saved successfully'}, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def fetch_jobs_by_student_skills(request):
    try:
        if request.method == 'GET':
            student_id = request.GET.get('student_id')

            if not student_id:
                return JsonResponse({'error': 'Please provide a student ID.'}, status=400)

            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return JsonResponse({'error': 'Student not found.'}, status=404)

            skills = student.skills
            skills_list = [skill.strip().lower() for skill in skills.split(',')] if skills else []

            jobs = Job.objects.all()
            if skills_list:
                queries = Q()
                for skill in skills_list:
                    queries |= Q(skills__icontains=skill)
                jobs = jobs.filter(queries).distinct()

            if not skills_list:
                return JsonResponse({'error': 'No skills found for this student.'}, status=400)

            job_list = []
            for job in jobs:
                job_list.append({
                    'company_name': job.company,
                    'job_title': job.job_title,
                    'location': job.location,
                    'job_type': job.job_type,
                })

            return JsonResponse({'jobs': job_list}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def create_job_alert(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action is None:
            return JsonResponse({'status': 'error', 'message': 'Action parameter is missing'}, status=400)
        
        if action == 'bookmark':
            return JsonResponse("Created Job Alerts Successfully", safe=False)

        elif action == 'apply':
            return JsonResponse("Applied Successfully", safe=False)
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)
    

