from django.utils import timezone
from hospital.models import Department, Doctor, Patient, Appointment, AIPrediction

cardiology = Department.objects.create(name ="Cardiology",  description="Heart and cardiovascular system disorders.")
neurology  = Department.objects.create(name ="Neurology",   description="Brain, spinal cord, and nervous system conditions.")
pediatrics = Department.objects.create(name ="Pediatrics",  description="Medical care for infants, children, and adolescents.")

dr_hassan = Doctor.objects.create(name="Hassan El-Dash", specialty="Interventional Cardiologist", email="h.eldash@hospital.com", department=cardiology)
dr_sara   = Doctor.objects.create(name="Sara Ali",       specialty="Neurologist",                 email="s.ali@hospital.com",    department=neurology)
dr_omar   = Doctor.objects.create(name="Omar Khalid",    specialty="Pediatrician",                email="o.khalid@hospital.com", department=pediatrics)

p1 = Patient.objects.create(name="Mona Tarek",   date_of_birth="1990-05-14", phone="+20-10-1234-5678")
p2 = Patient.objects.create(name="Karim Nasser", date_of_birth="1985-11-03", phone="+20-12-9876-5432")
p3 = Patient.objects.create(name="Lina Hassan",  date_of_birth="2012-07-22", phone="+20-11-5555-1234")

a1 = Appointment.objects.create(doctor=dr_hassan, patient=p1, date_time=timezone.now(), reason="Chest pain and shortness of breath for 3 days.", status=Appointment.SCHEDULED)
a2 = Appointment.objects.create(doctor=dr_sara,   patient=p2, date_time=timezone.now(), reason="Severe migraines with visual aura and nausea.",  status=Appointment.COMPLETED)
a3 = Appointment.objects.create(doctor=dr_omar,   patient=p3, date_time=timezone.now(), reason="Persistent high fever with maculopapular rash.",  status=Appointment.SCHEDULED)

AIPrediction.objects.create(appointment=a1, predicted_diagnosis="Unstable Angina Pectoris",   confidence_score=0.87, model_version="triage-v2.1", status=AIPrediction.SUCCESS, latency_ms=312)
AIPrediction.objects.create(appointment=a2, predicted_diagnosis="Migraine with Aura (G43.1)", confidence_score=0.94, model_version="triage-v2.1", status=AIPrediction.SUCCESS, latency_ms=278)
AIPrediction.objects.create(appointment=a3, predicted_diagnosis="Viral Exanthem — Roseola",   confidence_score=0.72, model_version="triage-v2.1", status=AIPrediction.SUCCESS, latency_ms=401)

print("All data created successfully")