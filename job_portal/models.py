from django.db import models # type: ignore
from django.utils import timezone # type: ignore

class Job(models.Model):
    company = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    experience_yr = models.CharField(max_length=10, default="0-100")
    job_title = models.CharField(max_length=200)
    job_type = models.CharField(max_length=50)
    experience = models.CharField(max_length=50)
    category =models.CharField(max_length=100)
    skills = models.CharField(max_length=1000, blank= False, null=False)
    workplaceTypes = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    questions = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.job_title


class Application(models.Model):
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    candidate_name = models.CharField(max_length=255, null=False, default="Unknown Candidate")
    email = models.EmailField(null=False, default="unknown@example.com")
    phone_number = models.CharField(max_length=15, default="123-456-7890")
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(default="No cover letter provided")
    applied_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='pending')
    skills = models.CharField(max_length=1000, blank= False, null=False)

    def __str__(self):
        return f"{self.candidate_name} - {self.job.job_title}"

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    website = models.URLField()
    description = models.TextField(max_length=255,default='description')
    sector_type = models.CharField(max_length=100)
    country_name  = models.CharField(max_length=50)


    def _str_(self):
        return self.name

class Resume(models.Model):
    first_name = models.CharField(max_length=100, default='John')
    last_name = models.CharField(max_length=100, default='John Doe')
    email = models.EmailField(default='example@example.com')
    phone = models.CharField(max_length=20, default='000-000-0000')
    address = models.TextField(default='N/A')
    date_of_birth = models.DateField(null=True, blank=True)
    website_urls = models.JSONField(default=list)  
    skills = models.TextField(default='Not specified')
    activities = models.TextField(default='None')
    interests = models.TextField(default='None')
    languages = models.TextField(default='None')
    bio = models.TextField(default='None')
    city = models.CharField(max_length=100, default='Mumbai')
    state = models.CharField(max_length=100, default='Maharashtra')
    country = models.CharField(max_length=100, default='India')
    zipcode = models.CharField(max_length=6, default='522426')
    Attachment = models.FileField(upload_to='attachments/',default='Unknown')
    delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Objective(models.Model):
    resume = models.OneToOneField(Resume, related_name='objective', on_delete=models.CASCADE)
    text = models.TextField(default='Not specified')

class Education(models.Model):
    resume = models.ForeignKey(Resume, related_name='education_entries', on_delete=models.CASCADE, default=1)
    course_or_degree = models.CharField(max_length=100, default='Unknown')
    school_or_university = models.CharField(max_length=100, default='Unknown')
    grade_or_cgpa = models.CharField(max_length=50, default='N/A')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.course_or_degree} at {self.school_or_university}"

class Experience(models.Model):
    resume = models.ForeignKey(Resume, related_name='experience_entries', on_delete=models.CASCADE,default=1)
    job_title = models.CharField(max_length=100, default='Unknown')
    company_name = models.CharField(max_length=100, default='Unknown')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(default='No description')

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class Project(models.Model):
    resume = models.ForeignKey(Resume, related_name='projects', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='Untitled Project')
    description = models.TextField(default='No description')

    def __str__(self):
        return self.title

class Reference(models.Model):
    resume = models.ForeignKey(Resume, related_name='references', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='Unknown')
    contact_info = models.CharField(max_length=100, default='Not provided')
    relationship = models.CharField(max_length=100, default='N/A')

    def __str__(self):
        return self.name
    
class Certification(models.Model):
   resume = models.ForeignKey(Resume, related_name='certifications', on_delete=models.CASCADE)
   name = models.CharField(max_length=100, default='Unknown')
   start_date = models.DateField(null=True, blank=True)
   end_date = models.DateField(null=True, blank=True)
 
class Achievements(models.Model):
    resume = models.ForeignKey(Resume, related_name='achievements', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='Unknown')
    publisher = models.CharField(max_length=100, default='Unknown')
    date_of_issue = models.DateField(null=True, blank=True)
    
class Publications(models.Model):
    resume = models.ForeignKey(Resume, related_name='publications', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='Unknown')
    publisher = models.CharField(max_length=100, default='Unknown')
    date_of_publications = models.DateField(null=True, blank=True)   


class CandidateStatus_selected(models.Model):
    candidate_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20,default='selected')
    company_name = models.CharField(max_length=255)
    job_id = models.IntegerField()

class CandidateStatus_rejected(models.Model):
    candidate_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20,default='rejected')
    company_name = models.CharField(max_length=255)
    job_id = models.IntegerField()

class CandidateStatus_not_eligible(models.Model):
    candidate_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20,default='not_eligible')
    company_name = models.CharField(max_length=255)
    job_id = models.IntegerField()

class CandidateStatus_under_review(models.Model):
    candidate_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20,default='under_review')
    company_name = models.CharField(max_length=255)
    job_id = models.IntegerField()
    
class User(models.Model):
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    email = models.CharField(max_length=50,unique=True)

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sender', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='recipient', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 
    # is_primary=models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

class Attachment(models.Model):
    message = models.ForeignKey('Message', related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
class Student(models.Model):
    first_name =  models.CharField(max_length=100, default='John')
    last_name = models.CharField(max_length=100, default='Doe')
    email = models.EmailField(default='example@example.com')
    contact_no = models.CharField(max_length=20, default='000-000-0000')
    qualification = models.TextField(default='N/A')
    skills = models.TextField(default='Not specified')    
    

     