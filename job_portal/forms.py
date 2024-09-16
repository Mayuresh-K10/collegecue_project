from django import forms # type: ignore
from .models import Achievements, Certification, Education, Experience, Job, Application, Company, Objective, Project, Publications, Reference, Resume, Student

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['job_title', 'company', 'location', 'description',
                   'requirements', 'job_type', 'experience', 'category',
                     'skills', 'experience_yr', 'workplaceTypes','questions']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['candidate_name', 'email', 'phone_number', 'resume', 'cover_letter', 'skills']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'city', 'state', 'country_name', 'website', 'sector_type' ,'description']

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['first_name','last_name', 'email', 'phone', 'address', 'date_of_birth', 'website_urls', 'skills', 'activities', 'interests', 'languages','bio','city','state','country','zipcode','Attachment','delete']

class ObjectiveForm(forms.ModelForm):
    class Meta:
        model = Objective
        fields = ['text']

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['course_or_degree', 'school_or_university', 'grade_or_cgpa', 'start_date', 'end_date']

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'description']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description']

class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = ['name', 'contact_info', 'relationship']
        
class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name','start_date','end_date']  
              
class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievements
        fields = ['title','publisher','date_of_issue']
          
class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publications
        fields = ['title', 'publisher', 'date_of_publications']
        
# class DeleteAccountForm(forms.Form):
    # confirm = forms.ChoiceField(choices=[('yes', 'Yes'), ('no', 'No')])
    
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'contact_no', 'qualification','skills']    