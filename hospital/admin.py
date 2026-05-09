"""
MediCore HMS Admin Panel Configuration
All five models are registered here
Appointment and AIPrediction use the @admin.register() decorator with
list_display and list_filter for clean, scannable admin views
"""

from django.contrib import admin
from .models import Department, Doctor, Patient, Appointment, AIPrediction


# Simple registrations 

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ("name", "description")
    search_fields = ("name",)
    ordering      = ("name",)




@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display  = ("name", "specialty", "department", "email")
    list_filter   = ("department",)
    search_fields = ("name", "specialty", "email")
    ordering      = ("name",)




@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display  = ("name", "date_of_birth", "phone")
    search_fields = ("name", "phone")
    ordering      = ("name",)




# Decorator registrations (required by spec) 
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ("__str__", "status", "date_time", "doctor", "patient", "created_at")
    list_filter   = ("status", "doctor__department", "date_time")
    search_fields = ("patient__name", "doctor__name", "reason")
    ordering      = ("-date_time",)
    readonly_fields = ("created_at",)
    date_hierarchy  = "date_time"




@admin.register(AIPrediction)
class AIPredictionAdmin(admin.ModelAdmin):
    list_display  = (
        "appointment",
        "status",
        "predicted_diagnosis",
        "confidence_percent",
        "model_version",
        "latency_ms",
        "created_at",
    )
    list_filter   = ("status", "model_version", "created_at")
    search_fields = ("appointment__patient__name", "predicted_diagnosis", "error_message")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at",)

    def confidence_percent(self, obj):
        return f"{obj.confidence_percent}%"
    confidence_percent.short_description = "Confidence"




# Admin site branding 
admin.site.site_header  = "MediCore HMS — Administration"
admin.site.site_title   = "MediCore Admin"
admin.site.index_title  = "Hospital Management Dashboard"
