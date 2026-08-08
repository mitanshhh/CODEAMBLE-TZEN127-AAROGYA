"use client";
import { apiFetch } from '@/lib/api';

import { useState, useEffect } from 'react';
import { Plus, MoreVertical, Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

// Types
interface HealthCentre {
  id: number;
  name: string;
  type: string;
  health_score: number;
  location: string;
  medical_officer: string;
  status: string;
}

export default function HealthCentreManagement() {
  const [centres, setCentres] = useState<HealthCentre[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modals state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  
  // Selected centre for view/edit
  const [selectedCentre, setSelectedCentre] = useState<HealthCentre | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    type: 'PHC',
    health_score: 100, // default
    location: '',
    medical_officer: '',
    status: 'Active',
    phc_id: '',
    admin_email: '',
    admin_mobile: ''
  });

  const [editFormData, setEditFormData] = useState<Partial<HealthCentre>>({});

  // Fetch centres
  const fetchCentres = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/phc/`, {
        headers: {
          'X-Role': 'DISTRICT_ADMIN'
        }
      });
      if (res.ok) {
        const data = await res.json();
        const mappedData = data.map((c: any) => ({
          ...c,
          status: c.status || 'Active',
          health_score: c.health_score || 95,
          location: c.district || 'Unknown',
          medical_officer: c.medical_officer || 'Unassigned'
        }));
        setCentres(mappedData);
      } else {
        toast.error("Failed to fetch health centres");
      }
    } catch (error) {
      toast.error("Network error: Could not reach backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCentres();
  }, []);

  // Handle register
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/phc/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Role': 'DISTRICT_ADMIN'
        },
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        toast.success("Health Centre registered & Email sent to Admin!");
        setIsRegisterOpen(false);
        setFormData({ name: '', type: 'PHC', health_score: 100, location: '', medical_officer: '', status: 'Active', phc_id: '', admin_email: '', admin_mobile: '' });
        fetchCentres();
      } else {
        const errorData = await res.json();
        toast.error(errorData.detail || "Failed to register Health Centre");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  // Handle edit
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCentre) return;
    
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/phc/${selectedCentre.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Role': 'DISTRICT_ADMIN'
        },
        body: JSON.stringify(editFormData)
      });
      
      if (res.ok) {
        toast.success("Health Centre updated successfully!");
        setIsEditOpen(false);
        fetchCentres();
      } else {
        toast.error("Failed to update Health Centre");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!selectedCentre) return;
    
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/phc/${selectedCentre.id}`, {
        method: 'DELETE',
        headers: {
          'X-Role': 'DISTRICT_ADMIN'
        }
      });
      
      if (res.ok) {
        toast.success("Health Centre deleted successfully!");
        setIsDeleteOpen(false);
        fetchCentres();
      } else {
        toast.error("Failed to delete Health Centre");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'optimal':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Active</Badge>;
      case 'critical':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Critical</Badge>;
      case 'maintenance':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">Maintenance</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-primary';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Filter states
  const [filterType, setFilterType] = useState<string>('All Types');
  const [filterDistrict, setFilterDistrict] = useState<string>('All Districts');
  const [filterStatus, setFilterStatus] = useState<string>('All Statuses');

  // Derived filter options
  const uniqueTypes = Array.from(new Set(centres.map(c => c.type)));
  const uniqueDistricts = Array.from(new Set(centres.map(c => c.location)));
  const uniqueStatuses = Array.from(new Set(centres.map(c => c.status)));

  // Filtered centres
  const filteredCentres = centres.filter(c => {
    if (filterType !== 'All Types' && c.type !== filterType) return false;
    if (filterDistrict !== 'All Districts' && c.location !== filterDistrict) return false;
    if (filterStatus !== 'All Statuses' && c.status.toLowerCase() !== filterStatus.toLowerCase()) return false;
    return true;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header Section */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">Health Centres</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage Primary and Community Health Centres</p>
        </div>
        
        {/* Register Dialog */}
        <Dialog open={isRegisterOpen} onOpenChange={setIsRegisterOpen}>
          <DialogTrigger render={
            <Button className="flex items-center gap-2 shadow-sm">
              <Plus className="w-4 h-4" />
              Register New PHC
            </Button>
          } />
          <DialogContent className="sm:max-w-[425px] rounded-xl border-border bg-card/95 backdrop-blur-md shadow-2xl">
            <DialogHeader>
              <DialogTitle>Register New Health Centre</DialogTitle>
              <DialogDescription>
                Enter the details of the new Primary or Community Health Centre. Click save when you're done.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleRegister}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="name" className="text-right text-sm font-medium">Name</label>
                  <Input 
                    id="name" 
                    placeholder="e.g. City Central Clinic" 
                    className="col-span-3 bg-background"
                    value={formData.name}
                    onChange={e => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label className="text-right text-sm font-medium">Type</label>
                  <div className="col-span-3">
                    <Select value={formData.type} onValueChange={(val) => setFormData({...formData, type: val || ''})}>
                      <SelectTrigger className="w-full bg-background text-foreground hover:border-primary/50">
                        <SelectValue placeholder="Select Type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PHC" className="cursor-pointer text-foreground">PHC (Primary Health Centre)</SelectItem>
                        <SelectItem value="CHC" className="cursor-pointer text-foreground">CHC (Community Health Centre)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="district" className="text-right text-sm font-medium">District</label>
                  <Input 
                    id="district" 
                    placeholder="e.g. North District" 
                    className="col-span-3 bg-background"
                    value={formData.location}
                    onChange={e => setFormData({...formData, location: e.target.value})}
                    required
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="officer" className="text-right text-sm font-medium">Officer</label>
                  <Input 
                    id="officer" 
                    placeholder="Medical Officer Name" 
                    className="col-span-3 bg-background"
                    value={formData.medical_officer}
                    onChange={e => setFormData({...formData, medical_officer: e.target.value})}
                    required
                  />
                </div>

                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="phc_id" className="text-right text-sm font-medium">PHC ID</label>
                  <Input 
                    id="phc_id" 
                    placeholder="e.g. CITY_01" 
                    className="col-span-3 bg-background"
                    value={formData.phc_id}
                    onChange={e => setFormData({...formData, phc_id: e.target.value})}
                    required
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="admin_email" className="text-right text-sm font-medium">Admin Email</label>
                  <Input 
                    id="admin_email" 
                    type="email"
                    className="col-span-3 bg-background"
                    value={formData.admin_email}
                    onChange={e => setFormData({...formData, admin_email: e.target.value})}
                    required
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="admin_mobile" className="text-right text-sm font-medium">Mobile</label>
                  <Input 
                    id="admin_mobile" 
                    className="col-span-3 bg-background"
                    value={formData.admin_mobile}
                    onChange={e => setFormData({...formData, admin_mobile: e.target.value})}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Save Centre</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="w-[180px]">
          <Select value={filterType} onValueChange={(v) => setFilterType(v ?? "")}>
            <SelectTrigger className="bg-card text-foreground hover:border-primary/50 shadow-sm">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Types" className="cursor-pointer text-foreground font-medium">All Types</SelectItem>
              {uniqueTypes.map(t => (
                <SelectItem key={t} value={t} className="cursor-pointer text-foreground">{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-[180px]">
          <Select value={filterDistrict} onValueChange={(v) => setFilterDistrict(v ?? "")}>
            <SelectTrigger className="bg-card text-foreground hover:border-primary/50 shadow-sm">
              <SelectValue placeholder="All Districts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Districts" className="cursor-pointer text-foreground font-medium">All Districts</SelectItem>
              {uniqueDistricts.map(d => (
                <SelectItem key={d} value={d} className="cursor-pointer text-foreground">{d}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-[180px]">
          <Select value={filterStatus} onValueChange={(v) => setFilterStatus(v ?? "")}>
            <SelectTrigger className="bg-card text-foreground hover:border-primary/50 shadow-sm">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Statuses" className="cursor-pointer text-foreground font-medium">All Statuses</SelectItem>
              {uniqueStatuses.map(s => (
                <SelectItem key={s} value={s} className="cursor-pointer text-foreground">{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Data Table Card */}
      <div className="bg-card rounded-xl border border-border overflow-hidden shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead className="font-semibold text-foreground">Name</TableHead>
              <TableHead className="font-semibold text-foreground">Type</TableHead>
              <TableHead className="font-semibold text-foreground">Health Score</TableHead>
              <TableHead className="font-semibold text-foreground">Location</TableHead>
              <TableHead className="font-semibold text-foreground">Medical Officer</TableHead>
              <TableHead className="font-semibold text-foreground">Status</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10">
                  <div className="flex justify-center items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" /> Fetching real-time data...
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredCentres.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10 text-muted-foreground">
                  No Health Centres found matching criteria.
                </TableCell>
              </TableRow>
            ) : (
              filteredCentres.map(centre => (
                <TableRow key={centre.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-medium">{centre.name}</TableCell>
                  <TableCell className="text-muted-foreground">{centre.type}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div className={`h-full ${getScoreColor(centre.health_score)}`} style={{ width: `${centre.health_score}%` }}></div>
                      </div>
                      <span className="text-sm font-medium">{centre.health_score}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{centre.location}</TableCell>
                  <TableCell>{centre.medical_officer}</TableCell>
                  <TableCell>
                    {getStatusBadge(centre.status)}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger className="inline-flex items-center justify-center h-8 w-8 rounded-full hover:bg-muted focus:outline-none cursor-pointer transition-all duration-200">
                        <MoreVertical className="h-4 w-4 text-muted-foreground" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="animate-in fade-in zoom-in duration-200">
                        <DropdownMenuItem 
                          className="cursor-pointer"
                          onClick={() => {
                            setSelectedCentre(centre);
                            setIsViewOpen(true);
                          }}
                        >
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          className="cursor-pointer"
                          onClick={() => {
                            setSelectedCentre(centre);
                            setEditFormData(centre);
                            setIsEditOpen(true);
                          }}
                        >
                          Edit Centre
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          className="cursor-pointer text-destructive focus:text-destructive focus:bg-destructive/10"
                          onClick={() => {
                            setSelectedCentre(centre);
                            setIsDeleteOpen(true);
                          }}
                        >
                          Delete Centre
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* View Details Dialog */}
      <Dialog open={isViewOpen} onOpenChange={setIsViewOpen}>
        <DialogContent className="sm:max-w-[425px] rounded-xl border-border bg-card/95 backdrop-blur-md shadow-2xl">
          <DialogHeader>
            <DialogTitle>Health Centre Details</DialogTitle>
            <DialogDescription>
              Comprehensive summary for {selectedCentre?.name}
            </DialogDescription>
          </DialogHeader>
          {selectedCentre && (
            <div className="grid gap-4 py-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Type</span>
                <span className="font-medium">{selectedCentre.type}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Location</span>
                <span className="font-medium">{selectedCentre.location}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Medical Officer</span>
                <span className="font-medium">{selectedCentre.medical_officer}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Health Score</span>
                <span className="font-medium">{selectedCentre.health_score}/100</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Status</span>
                <span>{getStatusBadge(selectedCentre.status)}</span>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsViewOpen(false)} className="cursor-pointer">Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Centre Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-[425px] rounded-xl border-border bg-card/95 backdrop-blur-md shadow-2xl">
          <DialogHeader>
            <DialogTitle>Edit Health Centre</DialogTitle>
            <DialogDescription>
              Make changes to {selectedCentre?.name}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEdit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <label className="text-right text-sm font-medium">Name</label>
                <Input 
                  className="col-span-3 bg-background"
                  value={editFormData.name || ''}
                  onChange={e => setEditFormData({...editFormData, name: e.target.value})}
                  required
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label className="text-right text-sm font-medium">Type</label>
                <div className="col-span-3">
                  <Select value={editFormData.type} onValueChange={(val) => setEditFormData({...editFormData, type: val || ''})}>
                    <SelectTrigger className="w-full bg-background text-foreground cursor-pointer">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PHC" className="cursor-pointer text-foreground">PHC</SelectItem>
                      <SelectItem value="CHC" className="cursor-pointer text-foreground">CHC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label className="text-right text-sm font-medium">Location</label>
                <Input 
                  className="col-span-3 bg-background"
                  value={editFormData.location || ''}
                  onChange={e => setEditFormData({...editFormData, location: e.target.value})}
                  required
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label className="text-right text-sm font-medium">Officer</label>
                <Input 
                  className="col-span-3 bg-background"
                  value={editFormData.medical_officer || ''}
                  onChange={e => setEditFormData({...editFormData, medical_officer: e.target.value})}
                  required
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label className="text-right text-sm font-medium">Status</label>
                <div className="col-span-3">
                  <Select value={editFormData.status} onValueChange={(val) => setEditFormData({...editFormData, status: val || ''})}>
                    <SelectTrigger className="w-full bg-background text-foreground cursor-pointer">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Active" className="cursor-pointer text-foreground">Active</SelectItem>
                      <SelectItem value="Critical" className="cursor-pointer text-foreground">Critical</SelectItem>
                      <SelectItem value="Maintenance" className="cursor-pointer text-foreground">Maintenance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>Cancel</Button>
              <Button type="submit">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent className="sm:max-w-[425px] rounded-xl border-border bg-card/95 backdrop-blur-md shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-destructive">Delete Health Centre</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{selectedCentre?.name}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => setIsDeleteOpen(false)}>Cancel</Button>
            <Button type="button" variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}




