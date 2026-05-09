from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name = 'dashboard'),

    # Departments
    path('departments/',          views.department_list,   name = 'department_list'),
    path('departments/<int:pk>/', views.department_detail, name = 'department_detail'),

    # Doctors
    path('doctors/',                 views.doctor_list,   name = 'doctor_list'),
    path('doctors/<int:pk>/',        views.doctor_detail, name = 'doctor_detail'),
    path('doctors/add/',             views.doctor_create, name = 'doctor_create'),
    path('doctors/<int:pk>/edit/',   views.doctor_edit,   name = 'doctor_edit'),
    path('doctors/<int:pk>/delete/', views.doctor_delete, name = 'doctor_delete'),

    # Patients
    path('patients/',                  views.patient_list,   name = 'patient_list'),
    path('patients/<int:pk>/',         views.patient_detail, name = 'patient_detail'),
    path('patients/add/',              views.patient_create, name = 'patient_create'),
    path('patients/<int:pk>/edit/',    views.patient_edit,   name = 'patient_edit'),
    path('patients/<int:pk>/delete/',  views.patient_delete, name = 'patient_delete'),

    # Appointments
    path('appointments/',                  views.appointment_list,   name = 'appointment_list'),
    path('appointments/<int:pk>/',         views.appointment_detail, name = 'appointment_detail'),
    path('appointments/add/',              views.appointment_create, name = 'appointment_create'),
    path('appointments/<int:pk>/edit/',    views.appointment_edit,   name = 'appointment_edit'),
    path('appointments/<int:pk>/delete/',  views.appointment_delete, name = 'appointment_delete'),

    # AI Predictions
    path('predictions/', views.prediction_list, name = 'prediction_list'),
]
