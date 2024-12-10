from django import forms
from .models import ExamParticipant, Notification, ProctoringEvent,Notification1,Notification2,Notification3

class StartProctoringSessionForm(forms.Form):
    exam_id = forms.IntegerField()
    duration = forms.DurationField(required=False, help_text="Duration of the session (e.g., '1:30:00' for 1 hour 30 minutes)")

class EndProctoringSessionForm(forms.Form):
    session_id = forms.IntegerField()

class RecordProctoringEventForm(forms.ModelForm):
    session_id = forms.IntegerField()

    class Meta:
        model = ProctoringEvent
        fields = ['event_type', 'details', 'session_id']

class SubmitAnswerForm(forms.Form):
    session_id = forms.IntegerField()
    question_no = forms.IntegerField()
    selected_option = forms.CharField(max_length=255)
    clear_response = forms.BooleanField(required=False)

class MarkForReviewForm(forms.Form):
    session_id = forms.IntegerField()
    question_no = forms.IntegerField()
    mark = forms.BooleanField()


class SubmitAllAnswersForm(forms.Form):
    session_id = forms.IntegerField()
    answers = forms.JSONField()

class ExamParticipantForm(forms.ModelForm):
    class Meta:
        model = ExamParticipant
        fields = ['name', 'email', 'phone_number']


class MarkAsReadForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['is_read']

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message']

class MarkAsReadForm1(forms.ModelForm):
    class Meta:
        model = Notification1
        fields = ['is_read']

class NotificationForm1(forms.ModelForm):
    class Meta:
        model = Notification1
        fields = ['user', 'title', 'message']

class MarkAsReadForm2(forms.ModelForm):
    class Meta:
        model = Notification2
        fields = ['is_read']

class NotificationForm2(forms.ModelForm):
    class Meta:
        model = Notification2
        fields = ['user', 'title', 'message']

class MarkAsReadForm3(forms.ModelForm):
    class Meta:
        model = Notification3
        fields = ['is_read']

class NotificationForm3(forms.ModelForm):
    class Meta:
        model = Notification3
        fields = ['user', 'title', 'message']


#k


