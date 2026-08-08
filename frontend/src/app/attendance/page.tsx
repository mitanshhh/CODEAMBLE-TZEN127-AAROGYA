"use client";

import { useState, useEffect } from 'react';
import MODashboard from '@/components/attendance/MODashboard';
import DoctorDashboard from '@/components/attendance/DoctorDashboard';
import { Loader2 } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { toast } from 'sonner';

export default function AttendancePage() {
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewAsDoctor, setViewAsDoctor] = useState(false);
  
  const searchParams = useSearchParams();

  useEffect(() => {
    // Check if coming back from Google Calendar OAuth
    if (searchParams.get("calendar_linked") === "true") {
      toast.success("Google Calendar successfully linked!");
      window.history.replaceState({}, '', '/attendance');
    }
  }, [searchParams]);

  useEffect(() => {
    const userRole = localStorage.getItem("role") || "MEDICAL_OFFICER";
    setRole(userRole);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const isMO = role === 'MEDICAL_OFFICER' || role === 'DISTRICT_ADMIN';
  const isDev = role === 'DEVELOPER';

  if (isDev) {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex justify-end bg-muted/50 p-2 rounded-lg border border-border">
          <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
            <input 
              type="checkbox" 
              checked={viewAsDoctor} 
              onChange={e => setViewAsDoctor(e.target.checked)}
              className="rounded border-primary/50 text-primary focus:ring-primary"
            />
            View as Doctor (Developer Toggle)
          </label>
        </div>
        {viewAsDoctor ? <DoctorDashboard /> : <MODashboard />}
      </div>
    );
  }

  if (isMO) {
    return <MODashboard />;
  }

  return <DoctorDashboard />;
}
