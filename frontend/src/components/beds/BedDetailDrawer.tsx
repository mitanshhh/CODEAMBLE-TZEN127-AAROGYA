import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Bed, User, Clock, CheckCircle2, UserPlus, LogOut, ArrowRight } from "lucide-react";
import { toast } from "sonner";

export function BedDetailDrawer({ bed, open, onOpenChange, onAdmit, onDischarge, onStatusChange }: any) {
  const { user } = useAuth();
  const allowedRoles = ["DISTRICT_ADMIN", "MEDICAL_OFFICER", "PHC_STAFF", "RECEPTIONIST", "DATA_ENTRY", "DEVELOPER"];
  const canManage = user?.role && allowedRoles.includes(user.role);
  
  const [patientName, setPatientName] = useState("");
  const [patientCode, setPatientCode] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [admissionReason, setAdmissionReason] = useState("");
  const [days, setDays] = useState("3");
  const [loading, setLoading] = useState(false);

  if (!bed) return null;

  const handleAdmit = async (action: string) => {
    if (!patientName) return toast.error("Patient name is required");
    setLoading(true);
    await onAdmit(bed.id, patientName, patientPhone, admissionReason, parseInt(days), action, patientCode);
    setLoading(false);
    onOpenChange(false);
  };

  const handleDischarge = async () => {
    setLoading(true);
    await onDischarge(bed.id);
    setLoading(false);
    onOpenChange(false);
  };

  const formatDateTime = (dateStr: any) => {
    if (!dateStr) return "--";
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return "--";
      return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' });
    } catch (e) {
      return "--";
    }
  };

  const getStatusBadgeStyles = (status: string) => {
    switch (status) {
      case 'Occupied': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Available': return 'bg-green-100 text-green-800 border-green-200';
      case 'Reserved': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'Cleaning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Maintenance': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Blocked': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-[480px] overflow-y-auto bg-background p-6">
        <SheetHeader className="mb-6 pb-4 border-b border-border/50">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-3">
              <SheetTitle className="text-xl font-bold flex items-center gap-2">
                <Bed className="w-5 h-5 text-primary" />
                Bed {bed.bed_number}
              </SheetTitle>
              <Badge variant="outline" className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${getStatusBadgeStyles(bed.status)}`}>
                {bed.status}
              </Badge>
            </div>
            <SheetDescription className="text-xs font-medium text-muted-foreground mt-1">
              {bed.ward} • {bed.bed_type}
            </SheetDescription>
          </div>
        </SheetHeader>

        <div className="space-y-6">
          {(bed.status === "Occupied" || bed.status === "Reserved") ? (
            <div className="bg-card p-5 rounded-xl border border-border shadow-sm space-y-4">
              <h3 className="font-semibold flex items-center gap-2 text-foreground text-sm border-b border-border/40 pb-2">
                <User className="w-4 h-4 text-blue-600" /> Patient Assignment ({bed.status})
              </h3>
              <div className="grid grid-cols-2 gap-y-4 gap-x-3 text-xs">
                <div>
                  <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider mb-1">Patient ID</p>
                  <p className="font-semibold text-primary">{bed.patient?.patient_code || bed.patient_code || (bed.patient_id ? `PT-${bed.patient_id.toString().padStart(4, '0')}` : "--")}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider mb-1">Patient Name</p>
                  <p className="font-medium text-foreground">{bed.patient_name || bed.patient?.name || "--"}</p>
                </div>
                {bed.patient_phone && (
                  <div>
                    <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider mb-1">Contact</p>
                    <p className="font-medium text-foreground">{bed.patient_phone}</p>
                  </div>
                )}
                {bed.admission_reason && (
                  <div>
                    <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider mb-1">Reason</p>
                    <p className="font-medium text-foreground">{bed.admission_reason}</p>
                  </div>
                )}
                <div>
                  <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider mb-1">Assigned Doctor</p>
                  <p className="font-medium text-foreground">{bed.doctor_name || "Unassigned"}</p>
                </div>
                <div className="col-span-2 mt-1 bg-muted/20 p-3 rounded-lg border border-border/50">
                  <p className="text-muted-foreground text-[10px] font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Clock className="w-3 h-3" /> Admission Timeline
                  </p>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-xs font-medium">
                    <div className="bg-background px-2.5 py-1 rounded border border-border/60 shadow-sm whitespace-nowrap">
                      {formatDateTime(bed.admission_time)}
                    </div>
                    <ArrowRight className="hidden sm:block w-3.5 h-3.5 text-muted-foreground/60 shrink-0" />
                    <div className="bg-background px-2.5 py-1 rounded border border-border/60 shadow-sm whitespace-nowrap">
                      {formatDateTime(bed.expected_discharge)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="pt-4 mt-2 flex justify-end gap-2">
                <Button variant="outline" size="sm" className="rounded-full px-5 transition-transform active:scale-95 hover:bg-muted cursor-pointer" onClick={() => onOpenChange(false)}>Close</Button>
                {canManage && bed.status === "Occupied" && (
                  <Button variant="destructive" size="sm" className="rounded-full px-5 gap-2 transition-transform active:scale-95 cursor-pointer" onClick={handleDischarge} disabled={loading}>
                    <LogOut className="w-3.5 h-3.5" /> Discharge Patient
                  </Button>
                )}
              </div>
            </div>
          ) : bed.status === "Available" ? (
            <div className="bg-card p-5 rounded-xl border border-border shadow-sm space-y-4">
              <h3 className="font-semibold flex items-center gap-2 text-green-700 text-sm border-b border-border/40 pb-2">
                <CheckCircle2 className="w-4 h-4" /> Ready for Admission
              </h3>
              <div className="space-y-4 pt-1 text-sm">
                <div className="space-y-2">
                  <Label>Patient ID / ABHA ID <span className="text-xs text-muted-foreground font-normal">(Optional)</span></Label>
                  <Input 
                    placeholder="e.g. PT-0001 or ABHA-1234 (Links existing patient)" 
                    value={patientCode}
                    onChange={e => setPatientCode(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Patient Name</Label>
                  <Input 
                    placeholder="Enter patient's full name" 
                    value={patientName}
                    onChange={e => setPatientName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone Number (Optional)</Label>
                  <Input 
                    placeholder="e.g. +91 98765 43210" 
                    value={patientPhone}
                    onChange={e => setPatientPhone(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Reason / Cause (Optional)</Label>
                  <Input 
                    placeholder="e.g. Dengue Fever, Accident..." 
                    value={admissionReason}
                    onChange={e => setAdmissionReason(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Expected Stay (Days)</Label>
                  <Input 
                    type="number" 
                    min="1"
                    value={days}
                    onChange={e => setDays(e.target.value)}
                  />
                </div>
              </div>
              <div className="pt-4 mt-2 flex items-center justify-end gap-2">
                <Button variant="outline" size="sm" className="rounded-full px-4 transition-transform active:scale-95 cursor-pointer hover:bg-muted" onClick={() => onOpenChange(false)}>Cancel</Button>
                <Button variant="secondary" size="sm" className="rounded-full px-4 font-semibold transition-transform active:scale-95 cursor-pointer" onClick={() => handleAdmit('Reserve')} disabled={loading}>
                  Reserve
                </Button>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 gap-2 text-white rounded-full px-4 font-semibold transition-transform active:scale-95 cursor-pointer" onClick={() => handleAdmit('Admit')} disabled={loading}>
                  <UserPlus className="w-3.5 h-3.5" /> Admit Patient
                </Button>
              </div>
            </div>
          ) : (
             <div className="bg-card p-6 rounded-xl border border-border shadow-sm space-y-3 text-center py-8">
                <p className="text-muted-foreground font-medium text-sm">This bed is currently <span className="font-bold text-foreground">{bed.status}</span> and cannot be assigned.</p>
                <div className="flex justify-center mt-4">
                  <Button variant="outline" size="sm" className="rounded-full px-6 transition-transform active:scale-95 cursor-pointer hover:bg-muted" onClick={() => onOpenChange(false)}>Close</Button>
                </div>
             </div>
          )}
          
          {/* Change Bed Status Section */}
          {canManage && (
            <div className="pt-6 mt-6 border-t border-border/50">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-primary"></span> Update Bed Status
              </p>
              <div className="grid grid-cols-3 gap-2">
                {['Available', 'Occupied', 'Cleaning', 'Maintenance', 'Reserved', 'Blocked'].map(status => (
                  <Button 
                    key={status} 
                    variant={bed.status === status ? "secondary" : "outline"} 
                    size="sm" 
                    className={`text-[11px] h-8 rounded-lg font-medium transition-all cursor-pointer ${bed.status === status ? 'pointer-events-none opacity-80' : 'hover:bg-muted hover:border-border active:scale-95'}`}
                    onClick={async () => {
                      setLoading(true);
                      await onStatusChange(bed.id, status);
                      setLoading(false);
                      onOpenChange(false);
                    }}
                    disabled={loading}
                  >
                    {status}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
