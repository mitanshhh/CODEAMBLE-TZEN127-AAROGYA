from app.models.user import UserRole

ROLE_PERMISSIONS = {
    UserRole.DEVELOPER: ["all"],
    UserRole.DISTRICT_ADMIN: ["view_district", "manage_district", "view_all_phc"],
    UserRole.MEDICAL_OFFICER: ["view_phc", "manage_phc", "manage_staff", "view_analytics", "generate_reports"],
    UserRole.DOCTOR: ["view_attendance"],
    UserRole.RECEPTIONIST: ["manage_patients"],
    UserRole.PHARMACIST: ["manage_inventory"],
    UserRole.LAB_TECHNICIAN: ["manage_inventory"],
    UserRole.DATA_ENTRY: ["manage_patients", "manage_beds", "manage_inventory"],
}
