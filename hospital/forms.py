from django import forms
from .models import Doctor, Patient, Appointment


class DoctorForm(forms.ModelForm):
    class Meta:
        model  = Doctor
        fields = ['name', 'specialty', 'email', 'department']
        widgets = {
            'name':       forms.TextInput(attrs  = {'placeholder': 'Full name'}),
            'specialty':  forms.TextInput(attrs  = {'placeholder': 'e.g. Cardiologist'}),
            'email':      forms.EmailInput(attrs = {'placeholder': 'doctor@hospital.com'}),
            'department': forms.Select(),
        }


class PatientForm(forms.ModelForm):
    class Meta:
        model   = Patient
        fields  = ['name', 'date_of_birth', 'phone']
        widgets = {
            'name':          forms.TextInput(attrs = {'placeholder': 'Full name'}),
            'date_of_birth': forms.DateInput(attrs = {'type': 'date'}),
            'phone':         forms.TextInput(attrs = {'placeholder': '+20-1X-XXXX-XXXX'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model   = Appointment
        fields  = ['doctor', 'patient', 'date_time', 'reason', 'status']
        widgets = {
            'doctor':    forms.Select(),
            'patient':   forms.Select(),
            'date_time': forms.DateTimeInput(attrs = {'type': 'datetime-local'}),
            'reason':    forms.Textarea(attrs = {'rows': 4, 'placeholder': 'Describe the reason for the appointment...'}),
            'status':    forms.Select(),
        }
