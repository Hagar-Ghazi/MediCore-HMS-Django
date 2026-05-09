from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    name        = models.CharField(max_length = 100, unique = True)
    description = models.TextField(blank = True , null = True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name




class Doctor(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete = models.PROTECT,
        related_name = "doctors",
    )
    name      = models.CharField(max_length = 100)
    specialty = models.CharField(max_length = 100)
    email     = models.EmailField(unique = True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Dr. {self.name}"




class Patient(models.Model):
    name          = models.CharField(max_length = 100)
    date_of_birth = models.DateField()
    phone         = models.CharField(max_length = 20)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name




class Appointment(models.Model):

    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Completed", "Completed"),
        ("Canceled",  "Canceled"),
    ]

    doctor     = models.ForeignKey(Doctor,  on_delete = models.PROTECT)
    patient    = models.ForeignKey(Patient, on_delete = models.PROTECT)
    date_time  = models.DateTimeField()
    reason     = models.TextField()
    status     = models.CharField(max_length = 20, choices = STATUS_CHOICES, default = 'Scheduled')
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-date_time"]
        default_related_name = "appointments"

    def __str__(self):
        return f"#{self.pk} --> {self.patient} --> Dr.{self.doctor}"





class AIPrediction(models.Model):

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED",  "Failed"),
    ]

    appointment         = models.ForeignKey(Appointment, on_delete = models.CASCADE, related_name = "predictions")
    predicted_diagnosis = models.CharField(max_length = 255, blank = True)
    confidence_score    = models.FloatField(
        default = 0.0,
        validators = [MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    model_version = models.CharField(max_length = 50)
    status        = models.CharField(max_length = 10, choices = STATUS_CHOICES, default = "SUCCESS")
    error_message = models.TextField(blank = True, null = True)
    token_count   = models.PositiveIntegerField(default = 0)
    latency_ms    = models.PositiveIntegerField(default = 0)
    created_at    = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.predicted_diagnosis} ({self.confidence_score:.0%})"

    @property
    def confidence_percent(self):
        return round(self.confidence_score * 100)
