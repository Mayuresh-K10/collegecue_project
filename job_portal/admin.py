from django.contrib import admin # type: ignore
from .models import  Achievements, CandidateStatus_rejected, CandidateStatus_under_review, Certification, Job, Application, Company, CandidateStatus_selected, CandidateStatus_not_eligible, Publications, Resume, Project, Objective, Experience, Education, Reference, User, Message, Attachment

admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Company)
admin.site.register(CandidateStatus_selected)
admin.site.register(CandidateStatus_rejected)
admin.site.register(CandidateStatus_not_eligible)
admin.site.register(CandidateStatus_under_review)
admin.site.register(Resume)
admin.site.register(Project)
admin.site.register(Reference)
admin.site.register(Publications)
admin.site.register(Experience)
admin.site.register(Education)
admin.site.register(Achievements)
admin.site.register(Certification)
admin.site.register(Objective)
admin.site.register(User)
admin.site.register(Message)
admin.site.register(Attachment)








