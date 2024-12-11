from django import forms # type: ignore
from .models import JobSeeker, Subscriber1,Consultant,Forgot2,UniversityInCharge,Subscriber,Verify,Forgot,CompanyInCharge

class CompanyInChargeForm(forms.ModelForm):
    class Meta:
        model = CompanyInCharge
        fields = ['company_name','official_email','country_code','mobile_number','password','linkedin_profile','company_person_name','agreed_to_terms']

class UniversityInChargeForm(forms.ModelForm):
    class Meta:
        model = UniversityInCharge
        fields = ['university_name','official_email','country_code','mobile_number','password','linkedin_profile','college_person_name','agreed_to_terms']


class ConsultantForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = ['consultant_name','official_email','country_code','mobile_number','password','linkedin_profile','consultant_person_name','agreed_to_terms']


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'})
}

class ForgotForm(forms.ModelForm):
    class Meta:
        model = Forgot
        fields = ['email']

class VerifyForm(forms.ModelForm):
    class Meta:
        model = Verify
        fields = ['otp']

class Forgot2Form(forms.ModelForm):
    class Meta:
        model = Forgot2
        fields = '__all__'

# class LoginForm(forms.ModelForm):
#     class Meta:
#         model = new_user
#         fields =['email','password']

class SubscriptionForm1(forms.ModelForm):
    class Meta:
        model = Subscriber1
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'})

}

class JobSeekerRegistrationForm(forms.ModelForm):
   class Meta:
      model = JobSeeker
      fields = ['first_name', 'last_name', 'email', 'mobile_number', 'password', 'country_code']
      widgets = {
         'password': forms.PasswordInput(),
    }

def clean_email(self):
        email = self.cleaned_data.get('email')
        if JobSeeker.objects.filter(email=email).exists():
         raise forms.ValidationError("Email already in use.")
        return email
