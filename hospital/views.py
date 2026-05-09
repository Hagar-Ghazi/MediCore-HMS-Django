"""
MediCore HMS — Views
──────────────────────────────────────────────────────────────────────
All views that modify data or trigger the AI pipeline are protected
by @login_required to prevent unauthorised access and API abuse.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .ai_service import run_diagnosis
from .forms import AppointmentForm, DoctorForm, PatientForm
from .models import AIPrediction, Appointment, Department, Doctor, Patient

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    total_patients     = Patient.objects.count()
    total_doctors      = Doctor.objects.count()
    total_appointments = Appointment.objects.count()
    total_departments  = Department.objects.count()

    scheduled = Appointment.objects.filter(status="Scheduled").count()
    completed = Appointment.objects.filter(status="Completed").count()
    canceled  = Appointment.objects.filter(status="Canceled").count()

    recent_appointments = (
        Appointment.objects
        .select_related("doctor", "patient")
        .order_by("-created_at")[:6]
    )
    recent_predictions = (
        AIPrediction.objects
        .select_related("appointment__patient", "appointment__doctor")
        .order_by("-created_at")[:5]
    )
    dept_stats = Department.objects.annotate(
        doctor_count=Count("doctors")
    ).order_by("-doctor_count")

    avg_confidence = (
        AIPrediction.objects
        .filter(status="SUCCESS")
        .aggregate(avg=Avg("confidence_score"))["avg"] or 0
    )
    avg_latency = (
        AIPrediction.objects
        .filter(status="SUCCESS")
        .aggregate(avg=Avg("latency_ms"))["avg"] or 0
    )

    return render(request, "hospital/dashboard.html", {
        "total_patients":      total_patients,
        "total_doctors":       total_doctors,
        "total_appointments":  total_appointments,
        "total_departments":   total_departments,
        "scheduled":           scheduled,
        "completed":           completed,
        "canceled":            canceled,
        "recent_appointments": recent_appointments,
        "recent_predictions":  recent_predictions,
        "dept_stats":          dept_stats,
        "avg_confidence":      round(avg_confidence * 100, 1),
        "avg_latency":         round(avg_latency, 1),
    })


# ─────────────────────────────────────────────────────────────────
#  Departments
# ─────────────────────────────────────────────────────────────────

@login_required
def department_list(request):
    departments = Department.objects.annotate(doctor_count=Count("doctors"))
    return render(request, "hospital/department_list.html", {"departments": departments})


@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    doctors    = department.doctors.all()
    return render(request, "hospital/department_detail.html", {
        "department": department,
        "doctors":    doctors,
    })


# ─────────────────────────────────────────────────────────────────
#  Doctors
# ─────────────────────────────────────────────────────────────────

@login_required
def doctor_list(request):
    q       = request.GET.get("q", "")
    dept_id = request.GET.get("dept", "")
    doctors = Doctor.objects.select_related("department")
    if q:
        doctors = doctors.filter(Q(name__icontains=q) | Q(specialty__icontains=q))
    if dept_id:
        doctors = doctors.filter(department_id=dept_id)
    departments = Department.objects.all()
    return render(request, "hospital/doctor_list.html", {
        "doctors":     doctors,
        "departments": departments,
        "q":           q,
        "dept_id":     dept_id,
    })


@login_required
def doctor_detail(request, pk):
    doctor       = get_object_or_404(Doctor, pk=pk)
    appointments = doctor.appointments.select_related("patient").order_by("-date_time")[:10]
    return render(request, "hospital/doctor_detail.html", {
        "doctor":       doctor,
        "appointments": appointments,
    })


@login_required
def doctor_create(request):
    form = DoctorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Doctor added successfully.")
        return redirect("doctor_list")
    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Add Doctor",
        "subtitle": "Register a new doctor to the system",
    })


@login_required
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    form   = DoctorForm(request.POST or None, instance=doctor)
    if form.is_valid():
        form.save()
        messages.success(request, "Doctor updated successfully.")
        return redirect("doctor_detail", pk=pk)
    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Edit Doctor",
        "subtitle": f"Editing Dr. {doctor.name}",
        "edit":     True,
    })


@login_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        doctor.delete()
        messages.success(request, "Doctor removed successfully.")
        return redirect("doctor_list")
    return render(request, "hospital/confirm_delete.html", {
        "object": doctor,
        "type":   "Doctor",
    })


# ─────────────────────────────────────────────────────────────────
#  Patients
# ─────────────────────────────────────────────────────────────────

@login_required
def patient_list(request):
    q        = request.GET.get("q", "")
    patients = Patient.objects.annotate(appointment_count=Count("appointments"))
    if q:
        patients = patients.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, "hospital/patient_list.html", {"patients": patients, "q": q})


@login_required
def patient_detail(request, pk):
    patient      = get_object_or_404(Patient, pk=pk)
    appointments = (
        patient.appointments
        .select_related("doctor", "doctor__department")
        .prefetch_related("predictions")
        .order_by("-date_time")
    )
    return render(request, "hospital/patient_detail.html", {
        "patient":      patient,
        "appointments": appointments,
    })


@login_required
def patient_create(request):
    form = PatientForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Patient registered successfully.")
        return redirect("patient_list")
    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Register Patient",
        "subtitle": "Add a new patient to the system",
    })


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form    = PatientForm(request.POST or None, instance=patient)
    if form.is_valid():
        form.save()
        messages.success(request, "Patient updated successfully.")
        return redirect("patient_detail", pk=pk)
    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Edit Patient",
        "subtitle": f"Editing {patient.name}",
        "edit":     True,
    })


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        patient.delete()
        messages.success(request, "Patient removed successfully.")
        return redirect("patient_list")
    return render(request, "hospital/confirm_delete.html", {
        "object": patient,
        "type":   "Patient",
    })


# ─────────────────────────────────────────────────────────────────
#  Appointments  ← AI pipeline lives here
# ─────────────────────────────────────────────────────────────────

@login_required
def appointment_list(request):
    status       = request.GET.get("status", "")
    q            = request.GET.get("q", "")
    appointments = Appointment.objects.select_related(
        "doctor", "patient", "doctor__department"
    )
    if status:
        appointments = appointments.filter(status=status)
    if q:
        appointments = appointments.filter(
            Q(patient__name__icontains=q) | Q(doctor__name__icontains=q)
        )
    return render(request, "hospital/appointment_list.html", {
        "appointments": appointments,
        "status":       status,
        "q":            q,
    })


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects
        .select_related("doctor", "patient", "doctor__department")
        .prefetch_related("predictions"),
        pk=pk,
    )
    return render(request, "hospital/appointment_detail.html", {
        "appointment": appointment,
    })


@login_required
def appointment_create(request):
    """
    Schedule a new appointment and automatically trigger the Ollama AI
    pipeline to generate a preliminary diagnosis from the patient's
    reported symptoms.

    Pipeline
    --------
    1. Validate the AppointmentForm.
    2. Save the Appointment (commit=False first, then save to get a PK).
    3. Call run_diagnosis() — wrapped in try/except via ai_service.
    4. Persist an AIPrediction record with SUCCESS or FAILED status.
    5. Redirect to the dashboard regardless of AI outcome.
    """
    form = AppointmentForm(request.POST or None)

    if form.is_valid():
        # Step 1: intercept the save to attach the AI result 
        appointment = form.save(commit=False)
        appointment.save()   # persisted — now has a primary key

        reason = appointment.reason

        # Step 2: run AI inference
        logger.info(
            "[Appointment #%d] Triggering AI diagnosis | reason=%s",
            appointment.pk,
            reason[:80],
        )

        result = run_diagnosis(reason)

        # Step 3: persist telemetry regardless of outcome 
        if result.success:
            AIPrediction.objects.create(
                appointment         = appointment,
                predicted_diagnosis = result.diagnosis,
                confidence_score    = result.confidence,
                model_version       = result.model_used,
                status              = "SUCCESS",
                token_count         = result.token_count,
                latency_ms          = result.latency_ms,
                error_message       = None,
            )
            messages.success(
                request,
                f"Appointment scheduled. AI assessment: {result.diagnosis} "
                f"(confidence {result.confidence:.0%})",
            )
            logger.info(
                "[Appointment #%d] AI SUCCESS | tokens=%d | latency=%dms",
                appointment.pk,
                result.token_count,
                result.latency_ms,
            )
        else:
            AIPrediction.objects.create(
                appointment         = appointment,
                predicted_diagnosis = "",
                confidence_score    = 0.0,
                model_version       = result.model_used or "unknown",
                status              = "FAILED",
                token_count         = 0,
                latency_ms          = result.latency_ms,
                error_message       = result.error,
            )
            messages.warning(
                request,
                "Appointment scheduled successfully. "
                "AI assessment could not be generated at this time — "
                "a staff member will review manually.",
            )
            logger.warning(
                "[Appointment #%d] AI FAILED | error=%s",
                appointment.pk,
                result.error,
            )

        return redirect("dashboard")

    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Schedule Appointment",
        "subtitle": "Book a new appointment — AI diagnosis will run automatically",
    })


@login_required
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    form        = AppointmentForm(request.POST or None, instance=appointment)
    if form.is_valid():
        form.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect("appointment_detail", pk=pk)
    return render(request, "hospital/form.html", {
        "form":     form,
        "title":    "Edit Appointment",
        "subtitle": f"Editing Appointment #{appointment.pk}",
        "edit":     True,
    })


@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        appointment.delete()
        messages.success(request, "Appointment removed successfully.")
        return redirect("appointment_list")
    return render(request, "hospital/confirm_delete.html", {
        "object": appointment,
        "type":   "Appointment",
    })


# ─────────────────────────────────────────────────────────────────
#  AI Predictions
# ─────────────────────────────────────────────────────────────────

@login_required
def prediction_list(request):
    predictions = (
        AIPrediction.objects
        .select_related("appointment__patient", "appointment__doctor")
        .order_by("-created_at")
    )
    avg_conf   = AIPrediction.objects.filter(status="SUCCESS").aggregate(avg=Avg("confidence_score"))["avg"] or 0
    avg_lat    = AIPrediction.objects.filter(status="SUCCESS").aggregate(avg=Avg("latency_ms"))["avg"] or 0
    success_ct = AIPrediction.objects.filter(status="SUCCESS").count()
    total_ct   = AIPrediction.objects.count()

    return render(request, "hospital/prediction_list.html", {
        "predictions":    predictions,
        "avg_confidence": round(avg_conf * 100, 1),
        "avg_latency":    round(avg_lat, 1),
        "success_count":  success_ct,
        "total_count":    total_ct,
    })
