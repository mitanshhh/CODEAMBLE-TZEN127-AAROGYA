"use client";
import { apiFetch } from '@/lib/api';

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Search, Filter, RefreshCw, X, ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { PatientAnalyticsCards } from "@/components/patients/PatientAnalyticsCards";
import { PatientForm } from "@/components/patients/PatientForm";

import { useAuth } from '@/contexts/AuthContext';

export default function PatientsPage() {
  const { user, selectedHospitalId } = useAuth();
  const [patients, setPatients] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedActionPatient, setSelectedActionPatient] = useState<any>(null);
  const [isEditingPatient, setIsEditingPatient] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: "",
    age: "",
    gender: "",
    contact: "",
    medical_history: ""
  });
  const [role, setRole] = useState("DEVELOPER");
  
  // Will be fetched from backend

  const fetchData = async () => {
    setLoading(true);
    try {
      const hospitalQuery = selectedHospitalId ? `?hospital_id=${selectedHospitalId}` : '';
      // Fetch patients
      const pRes = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/${hospitalQuery}`);
      if (pRes.ok) {
        const pData = await pRes.json();
        setPatients(pData.data || []);
      }
      
      // Fetch analytics
      const aRes = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/analytics${hospitalQuery}`);
      if (aRes.ok) {
        const aData = await aRes.json();
        setAnalytics(aData);
      }
      
      // Fetch doctors
      const dRes = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/doctors${hospitalQuery}`);
      if (dRes.ok) {
        const dData = await dRes.json();
        setDoctors(dData);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => { const r = localStorage.getItem("role") || "DEVELOPER"; setRole(r); fetchData(); }, [selectedHospitalId]);

  const handleRegisterPatient = async (data: any) => {
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data })
      });
      if (res.ok) {
        setIsFormOpen(false);
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const updateStatus = async (id: number, status: string) => {
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filteredPatients = patients.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || String(p.id).includes(search);
    const matchesStatus = statusFilter === "All" || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleEditPatientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedActionPatient) return;
    
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/${selectedActionPatient.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editFormData.name,
          age: parseInt(editFormData.age) || 0,
          gender: editFormData.gender,
          contact: editFormData.contact,
          medical_history: editFormData.medical_history
        })
      });
      
      if (!res.ok) throw new Error("Failed to update patient");
      
      toast.success("Patient details updated successfully");
      setIsEditingPatient(false);
      setSelectedActionPatient(null);
      fetchData();
    } catch (error) {
      console.error(error);
      toast.error("Error updating patient");
    }
  };

  const openPatientEdit = (patient: any) => {
    setSelectedActionPatient(patient);
    setEditFormData({
      name: patient.name || "",
      age: patient.age?.toString() || "",
      gender: patient.gender || "",
      contact: patient.contact || "",
      medical_history: patient.medical_history || ""
    });
    setIsEditingPatient(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Waiting": return "bg-amber-100 text-amber-800 border-amber-200";
      case "Under Consultation": return "bg-blue-100 text-blue-800 border-blue-200";
      case "Completed": return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "Cancelled": return "bg-red-100 text-red-800 border-red-200";
      case "Referred": return "bg-purple-100 text-purple-800 border-purple-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "Critical": return "bg-red-500 text-white border-transparent";
      case "Urgent": return "bg-orange-500 text-white border-transparent";
      default: return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6 max-w-7xl mx-auto w-full relative">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Patient Registration</h2>
          <p className="text-muted-foreground mt-1">Manage patient footfall, triage, and department loads.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={fetchData} disabled={loading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {(role === "PHC_STAFF" || role === "DEVELOPER" || role === "MEDICAL_OFFICER") && (
            <Button onClick={() => setIsFormOpen(true)} className="gap-2 shadow-lg shadow-primary/20">
              <Plus className="w-4 h-4" />
              New Patient
            </Button>
          )}
        </div>
      </div>

      {analytics && <PatientAnalyticsCards kpis={analytics.kpis} charts={analytics.charts} />}

      <div className="bg-card rounded-xl border border-border overflow-hidden shadow-sm flex flex-col mt-6">
        <div className="p-4 border-b border-border bg-muted/20 flex flex-col md:flex-row gap-4 justify-between items-center">
          <div className="flex items-center gap-3 w-full md:w-1/2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="Search by ID or Name..." 
                className="pl-9 bg-background"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "")}>
                <SelectTrigger className="w-[140px] bg-background">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Statuses</SelectItem>
                  <SelectItem value="Waiting">Waiting</SelectItem>
                  <SelectItem value="Under Consultation">Consulting</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow>
                <TableHead className="w-[100px]">ID</TableHead>
                <TableHead>Patient Info</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Arrival Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Edit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && patients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
                    Loading patients...
                  </TableCell>
                </TableRow>
              ) : filteredPatients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                    No patients found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredPatients.map((p) => (
                  <TableRow key={p.id} className="hover:bg-muted/30 transition-colors group">
                    <TableCell className="font-semibold text-primary">PT-{p.id.toString().padStart(4, '0')}</TableCell>
                    <TableCell>
                      <div className="font-medium">{p.name}</div>
                      <div className="text-xs text-muted-foreground">{p.age}y • {p.gender}</div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-sm">General</div>
                      <div className="text-xs text-muted-foreground">OPD</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getPriorityColor("Normal")}>
                        Normal
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground font-medium">
                      {p.admitted_at ? new Date(p.admitted_at).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute:'2-digit' }) : '--:--'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className={getStatusColor(p.status)}>
                          {p.status}
                        </Badge>
                        {p.status === "Waiting" && (
                          <Button size="sm" variant="outline" onClick={() => updateStatus(p.id, "Consultation")} className="text-xs h-7 px-2 text-blue-600 border-blue-200 hover:bg-blue-50 cursor-pointer">
                            → Consult
                          </Button>
                        )}
                        {p.status === "Consultation" && (
                          <Button size="sm" variant="outline" onClick={() => updateStatus(p.id, "Checkup")} className="text-xs h-7 px-2 text-orange-600 border-orange-200 hover:bg-orange-50 cursor-pointer">
                            → Checkup
                          </Button>
                        )}
                        {p.status === "Checkup" && (
                          <Button size="sm" variant="outline" onClick={() => updateStatus(p.id, "Completed")} className="text-xs h-7 px-2 text-emerald-600 border-emerald-200 hover:bg-emerald-50 cursor-pointer">
                            → Complete
                          </Button>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="ghost" onClick={() => openPatientEdit(p)} className="h-8 w-8 p-0 cursor-pointer hover:bg-muted" title="Edit patient">
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <Sheet open={isFormOpen} onOpenChange={setIsFormOpen}>
        <SheetContent side="right" className="w-full md:w-[600px] sm:max-w-none p-0 border-l border-border bg-background">
          <PatientForm 
            onSubmit={handleRegisterPatient} 
            onClose={() => setIsFormOpen(false)}
            doctors={doctors}
          />
        </SheetContent>
      </Sheet>

      <Dialog open={isEditingPatient} onOpenChange={(open) => !open && setIsEditingPatient(false)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Patient Details</DialogTitle>
            <DialogDescription>
              Update information for PT-{selectedActionPatient?.id?.toString().padStart(4, '0')} - {selectedActionPatient?.name}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditPatientSubmit} className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input 
                  id="name" 
                  value={editFormData.name} 
                  onChange={(e) => setEditFormData({...editFormData, name: e.target.value})} 
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact">Contact Number</Label>
                <Input 
                  id="contact" 
                  value={editFormData.contact} 
                  onChange={(e) => setEditFormData({...editFormData, contact: e.target.value})} 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="age">Age</Label>
                <Input 
                  id="age" 
                  type="number" 
                  value={editFormData.age} 
                  onChange={(e) => setEditFormData({...editFormData, age: e.target.value})} 
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gender">Gender</Label>
                <Select value={editFormData.gender} onValueChange={(v) => setEditFormData({...editFormData, gender: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Male">Male</SelectItem>
                    <SelectItem value="Female">Female</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="medical_history">Medical History / Symptoms</Label>
              <textarea 
                id="medical_history" 
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={editFormData.medical_history} 
                onChange={(e) => setEditFormData({...editFormData, medical_history: e.target.value})} 
              />
            </div>
            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setIsEditingPatient(false)}>Cancel</Button>
              <Button type="submit">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
