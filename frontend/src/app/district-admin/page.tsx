"use client";
import { apiFetch } from '@/lib/api';
import { useEffect, useState } from 'react';
import { Download, Hospital, Building2, Stethoscope, BedDouble, AlertTriangle, AlertOctagon, Sparkles, MapPin, CheckCircle, X, Bot } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import dynamic from 'next/dynamic';



export default function DistrictAdminDashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [requests, setRequests] = useState<any[]>([]);
  const [mapData, setMapData] = useState<any[]>([]);
  const [selectedReq, setSelectedReq] = useState<any>(null);
  const [customReply, setCustomReply] = useState("");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [newPhc, setNewPhc] = useState({
    name: "", type: "PHC", phc_id: "", admin_email: "", admin_mobile: "", location: ""
  });

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token") || "mock_token";
      const role = localStorage.getItem("role") || "DISTRICT_ADMIN";
      const opts = { headers: { "Authorization": `Bearer ${token}`, "X-Role": role } };
      
      const [resOverview, resReq, resMap] = await Promise.all([
        apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/district/overview`, opts),
        apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/district/requests`, opts),
        apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/district/map-data`, opts)
      ]);
      
      if(resOverview.ok) setOverview(await resOverview.json());
      if(resReq.ok) setRequests(await resReq.json());
      if(resMap.ok) setMapData(await resMap.json());
    } catch (e) {
      console.error(e);
      toast.error("Failed to load district data");
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async () => {
    if(!selectedReq) return;
    try {
      const token = localStorage.getItem("token") || "mock_token";
      const role = localStorage.getItem("role") || "DISTRICT_ADMIN";
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/district/resource-request/${selectedReq.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}`, "X-Role": role },
        body: JSON.stringify({ status: "APPROVED", admin_note: customReply })
      });
      if(res.ok) {
        toast.success("Request approved! AI letter sent to PHC.");
        setSelectedReq(null);
        setCustomReply("");
        fetchData();
      } else {
        toast.error("Approval failed.");
      }
    } catch (e) {
      console.error(e);
      toast.error("Network error");
    }
  };

  const handleReject = async () => {
    if(!selectedReq) return;
    try {
      const token = localStorage.getItem("token") || "mock_token";
      const role = localStorage.getItem("role") || "DISTRICT_ADMIN";
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/district/resource-request/${selectedReq.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}`, "X-Role": role },
        body: JSON.stringify({ status: "REJECTED", admin_note: customReply })
      });
      if(res.ok) {
        toast.success("Request rejected.");
        setSelectedReq(null);
        setCustomReply("");
        fetchData();
      } else {
        toast.error("Rejection failed.");
      }
    } catch (e) {
      console.error(e);
      toast.error("Network error");
    }
  };

  const handleRegisterPhc = async () => {
    if (!newPhc.phc_id || !newPhc.admin_email) {
      toast.error("PHC ID and Admin Email are required");
      return;
    }
    
    // Geocode location to get lat/lng
    let lat = 0.0;
    let lng = 0.0;
    if (newPhc.location && window.google) {
      try {
        const geocoder = new window.google.maps.Geocoder();
        const results = await geocoder.geocode({ address: newPhc.location });
        if (results.results && results.results.length > 0) {
          lat = results.results[0].geometry.location.lat();
          lng = results.results[0].geometry.location.lng();
        }
      } catch (e) {
        console.warn("Geocoding failed", e);
      }
    }

    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/phc/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newPhc,
          district: newPhc.location || "North District",
          state: "Maharashtra",
          health_score: 100,
          status: "Active",
          latitude: lat,
          longitude: lng
        })
      });
      if (res.ok) {
        toast.success("PHC Registered & Email Sent to Admin!");
        setIsRegisterOpen(false);
        setNewPhc({ name: "", type: "PHC", phc_id: "", admin_email: "", admin_mobile: "", location: "" });
        fetchData();
      } else {
        const err = await res.json();
        let errorMsg = "Registration failed";
        if (typeof err.detail === 'string') {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map((e: any) => `${e.loc?.join('.')} ${e.msg}`).join(', ');
        }
        toast.error(errorMsg);
      }
    } catch (e) {
      toast.error("Network error");
    }
  };

  const pendingRequests = requests.filter(r => r.status === "PENDING");
  const historyRequests = requests.filter(r => r.status !== "PENDING").reverse();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-end mb-2">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">District Overview</h2>
          <p className="text-sm text-muted-foreground mt-1">Live operational status and resource allocation.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" className="flex items-center gap-2" onClick={() => setIsRegisterOpen(true)}>
            <Building2 className="w-4 h-4" /> Register New PHC
          </Button>
          <Button className="flex items-center gap-2">
            <Download className="w-4 h-4" /> Export Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* KPI Grid */}
        <div className="col-span-12 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary"><Hospital className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Total PHCs</h3></div>
            <div className="text-2xl font-bold text-foreground">{overview?.total_phcs || 0}</div>
          </CardContent></Card>
          
          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary"><Building2 className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Total CHCs</h3></div>
            <div className="text-2xl font-bold text-foreground">{overview?.total_chcs || 0}</div>
          </CardContent></Card>
          
          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-green-100 flex items-center justify-center text-green-700"><Stethoscope className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Doctors</h3></div>
            <div className="text-2xl font-bold text-foreground">{overview?.doctor_presence_rate || 0}%</div>
          </CardContent></Card>
          
          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-secondary flex items-center justify-center text-secondary-foreground"><BedDouble className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Beds</h3></div>
            <div className="text-2xl font-bold text-foreground">{overview?.bed_occupancy_rate || 0}%</div>
            <div className="w-full bg-secondary h-1 rounded-full mt-2 overflow-hidden"><div className="bg-primary h-full rounded-full" style={{ width: `${overview?.bed_occupancy_rate || 0}%` }}></div></div>
          </CardContent></Card>

          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-yellow-100 flex items-center justify-center text-yellow-600"><AlertTriangle className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-yellow-600 uppercase tracking-wider">Meds</h3></div>
            <div className="text-2xl font-bold text-yellow-600">{overview?.medicine_alerts || 0}</div>
          </CardContent></Card>

          <Card className="border-border shadow-none hover:shadow-md transition-shadow"><CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2"><div className="w-8 h-8 rounded bg-red-100 flex items-center justify-center text-red-600"><AlertOctagon className="w-4 h-4" /></div><h3 className="text-xs font-semibold text-red-600 uppercase tracking-wider">Critical</h3></div>
            <div className="text-2xl font-bold text-red-600">{overview?.critical_centres || 0}</div>
          </CardContent></Card>
        </div>

        {/* AI Resource Optimization and Requests */}
        <div className="col-span-12 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-border shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
            <CardContent className="p-6 flex flex-col h-full overflow-hidden">
              <div className="flex items-center gap-2 mb-4 text-foreground">
                <AlertTriangle className="w-5 h-5 text-muted-foreground" />
                <h3 className="text-sm font-bold">Resource Requests</h3>
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                  {pendingRequests.length} Pending
                </span>
              </div>
              
              <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                {pendingRequests.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground text-sm">No pending requests</div>
                ) : (
                  pendingRequests.map((req) => (
                    <div key={req.id} onClick={() => setSelectedReq(req)} className="bg-muted/30 rounded-lg p-3 border border-border cursor-pointer hover:border-primary/50 hover:bg-muted/50 transition-colors">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="text-sm font-semibold text-foreground">Request: {req.resource_name}</h4>
                        <span className="text-[10px] text-muted-foreground bg-white px-1.5 py-0.5 rounded border border-border">{new Date(req.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">From PHC ID: {req.requesting_phc_id}</p>
                      <p className="text-xs text-foreground/80 line-clamp-2">{req.message}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-border shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
            <CardContent className="p-6 flex flex-col h-full overflow-hidden">
              <div className="flex items-center gap-2 mb-4 text-foreground">
                <CheckCircle className="w-5 h-5 text-muted-foreground" />
                <h3 className="text-sm font-bold">Request History</h3>
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                  {historyRequests.length} Handled
                </span>
              </div>
              
              <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                {historyRequests.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground text-sm">No history available</div>
                ) : (
                  historyRequests.map((req) => (
                    <div key={req.id} className="bg-muted/30 rounded-lg p-3 border border-border transition-colors">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="text-sm font-semibold text-foreground">Request: {req.resource_name}</h4>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${req.status === 'APPROVED' ? 'text-green-600 bg-green-50 border-green-200' : 'text-red-600 bg-red-50 border-red-200'}`}>
                          {req.status}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">From PHC ID: {req.requesting_phc_id}</p>
                      <p className="text-xs text-foreground/80 line-clamp-2 mb-2">{req.message}</p>
                      <p className="text-[10px] text-muted-foreground italic">Admin Note: {req.admin_note || "None"}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={!!selectedReq} onOpenChange={() => setSelectedReq(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Evaluate Resource Request</DialogTitle>
            <DialogDescription>
              Review the request for <strong>{selectedReq?.resource_name}</strong> from PHC ID <strong>{selectedReq?.requesting_phc_id}</strong>.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <div className="bg-muted/30 p-3 rounded-lg border border-border text-sm mb-4">
              <span className="font-semibold text-foreground block mb-1">PHC Notes:</span>
              <span className="text-muted-foreground">{selectedReq?.notes || "No additional notes provided."}</span>
            </div>
            
            <h4 className="font-semibold text-sm mb-1">Admin Reply (Optional):</h4>
            <Textarea 
              placeholder="Add a custom note to the AI-generated approval letter..." 
              value={customReply}
              onChange={(e) => setCustomReply(e.target.value)}
              className="resize-none h-20"
            />
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> An AI approval letter will be sent automatically.
            </p>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setSelectedReq(null)}>Cancel</Button>
            <Button onClick={handleReject} className="bg-red-100 text-red-600 hover:bg-red-600 hover:text-white cursor-pointer transition-colors border-none"><X className="w-4 h-4 mr-2" /> Reject</Button>
            <Button onClick={handleApprove} className="flex items-center gap-2 cursor-pointer hover:shadow-md transition-shadow"><CheckCircle className="w-4 h-4" /> Approve & Notify</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isRegisterOpen} onOpenChange={setIsRegisterOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Register New PHC / CHC</DialogTitle>
            <DialogDescription>Add a new health centre and automatically invite its admin.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Centre Name</Label>
              <Input 
                placeholder="Enter centre name" 
                value={newPhc.name} 
                onChange={e => setNewPhc({...newPhc, name: e.target.value})} 
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Type</Label>
                <select 
                  className="w-full flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={newPhc.type}
                  onChange={e => setNewPhc({...newPhc, type: e.target.value})}
                >
                  <option value="PHC">PHC</option>
                  <option value="CHC">CHC</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>Unique ID (PHC_ID)</Label>
                <Input 
                  placeholder="Enter unique ID" 
                  value={newPhc.phc_id} 
                  onChange={e => setNewPhc({...newPhc, phc_id: e.target.value})} 
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Location</Label>
              <Input 
                placeholder="Enter location" 
                value={newPhc.location} 
                onChange={e => setNewPhc({...newPhc, location: e.target.value})} 
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Admin Email ID</Label>
                <Input 
                  type="email"
                  value={newPhc.admin_email} 
                  onChange={e => setNewPhc({...newPhc, admin_email: e.target.value})} 
                />
              </div>
              <div className="space-y-2">
                <Label>Admin Mobile (Optional)</Label>
                <Input 
                  value={newPhc.admin_mobile} 
                  onChange={e => setNewPhc({...newPhc, admin_mobile: e.target.value})} 
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRegisterOpen(false)}>Cancel</Button>
            <Button onClick={handleRegisterPhc} className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> Register Centre
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


