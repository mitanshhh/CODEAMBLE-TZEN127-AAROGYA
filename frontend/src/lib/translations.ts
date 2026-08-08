export type Locale = 'en' | 'hi' | 'mr';

export const LOCALE_LABELS: Record<Locale, { native: string; label: string }> = {
  en: { native: 'EN', label: 'English' },
  hi: { native: 'HI', label: 'हिंदी (Hindi)' },
  mr: { native: 'MR', label: 'मराठी (Marathi)' }
};

export const TRANSLATION_KEYS: Record<string, string> = {
  'nav.dashboard': 'Dashboard',
  'nav.healthCentres': 'Health Centres',
  'nav.inventory': 'Inventory',
  'nav.doctors': 'Doctors',
  'nav.patients': 'Patients',
  'nav.beds': 'Bed Management',
  'nav.analytics': 'Analytics',
  'nav.aiReports': 'AI Reports',
  'nav.manageRoles': 'Manage Roles',
  'header.viewingDataFor': 'Viewing Data For',
  'header.searchHospitals': 'Search Hospitals...',
  'header.noHospitalsFound': 'No hospitals found.',
  'header.searchFacilities': 'Search facilities, patients, resources...',
  'header.notifications': 'Notifications',
  'header.new': 'New',
  'header.noNotifications': 'No new notifications',
  'header.role': 'Role',
  'header.primaryCentre': 'Primary Centre',
  'header.systemWide': 'System Wide',
  'header.logout': 'Logout',
  'header.markAsRead': 'Mark as Read'
};
