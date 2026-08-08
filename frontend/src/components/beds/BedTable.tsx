"use client";

import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, UserPlus, FileMinus } from "lucide-react";
import { BedDetailDrawer } from "./BedDetailDrawer";

interface BedTableProps {
  beds: any[];
  onAdmit: (bedId: number, patientName: string, phone: string, reason: string, days: number, action: string) => void;
  onDischarge: (bedId: number) => void;
  onStatusChange: (bedId: number, status: string) => void;
  onEdit?: (bed: any) => void;
}

export function BedTable({ beds, onAdmit, onDischarge, onStatusChange, onEdit }: BedTableProps) {
  const [search, setSearch] = useState("");
  const [selectedBed, setSelectedBed] = useState<any>(null);
  
  const filteredBeds = beds.filter(b => 
    b.bed_number.toLowerCase().includes(search.toLowerCase()) || 
    (b.patient_name && b.patient_name.toLowerCase().includes(search.toLowerCase())) ||
    b.ward.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Available": return "bg-green-100 text-green-700 border-green-200";
      case "Occupied": return "bg-blue-100 text-blue-700 border-blue-200";
      case "Reserved": return "bg-purple-100 text-purple-700 border-purple-200";
      case "Cleaning": return "bg-yellow-100 text-yellow-700 border-yellow-200";
      case "Maintenance": return "bg-orange-100 text-orange-700 border-orange-200";
      case "Blocked": return "bg-red-100 text-red-700 border-red-200";
      default: return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-border/50 shadow-sm">
        <div className="relative w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search bed, patient, or ward..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-9"
          />
        </div>
        <div className="flex gap-2">
          {/* We could put quick filters here */}
        </div>
      </div>
      
      <div className="border border-border/50 rounded-xl overflow-hidden bg-white shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead>Bed</TableHead>
              <TableHead>Ward</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Patient</TableHead>
              <TableHead>Admission Time</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredBeds.map(bed => (
              <TableRow key={bed.id} className="hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => setSelectedBed(bed)}>
                <TableCell className="font-semibold">{bed.bed_number}</TableCell>
                <TableCell>{bed.ward}</TableCell>
                <TableCell className="text-muted-foreground text-sm">{bed.bed_type}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={`${getStatusColor(bed.status)}`}>
                    {bed.status}
                  </Badge>
                </TableCell>
                <TableCell className="font-medium">{bed.patient_name || "--"}</TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {bed.admission_time ? new Date(bed.admission_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' }) : "--"}
                </TableCell>
                <TableCell className="text-right space-x-2">
                  {onEdit && (
                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onEdit(bed); }}>
                      Edit
                    </Button>
                  )}
                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); setSelectedBed(bed); }}>
                    Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {filteredBeds.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No beds match your search criteria.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <BedDetailDrawer 
        bed={selectedBed} 
        open={!!selectedBed} 
        onOpenChange={(val: boolean) => !val && setSelectedBed(null)} 
        onAdmit={onAdmit}
        onDischarge={onDischarge}
        onStatusChange={onStatusChange}
      />
    </div>
  );
}
