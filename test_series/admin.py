from django.contrib import admin
from .models import Exam, ExamParticipant, ProctoringSession, ProctoringEvent, Question, UserResponse, UserScore,Notification,Notification1,Notification2,Notification3

admin.site.register(Exam)
admin.site.register(ProctoringSession)
admin.site.register(ProctoringEvent)
admin.site.register(Question)
admin.site.register(UserResponse)
admin.site.register(UserScore)
admin.site.register(ExamParticipant)
admin.site.register(Notification)
admin.site.register(Notification1)
admin.site.register(Notification2)
admin.site.register(Notification3)



#k