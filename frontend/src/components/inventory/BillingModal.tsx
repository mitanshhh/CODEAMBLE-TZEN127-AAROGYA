import React, { useState, useEffect } from 'react';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FileText, Loader2 } from 'lucide-react';
import { toast } from "sonner";
import { apiFetch } from '@/lib/api';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { PatientSearchInput } from '../patients/PatientSearchInput';

interface SelectedMedicine {
  id: number;
  name: string;
  quantity: number;
  price: number;
  maxQty: number;
  originalQtySold: number;
}

interface BillingModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  hospitalName: string;
  selectedMedicines: SelectedMedicine[];
  onSuccess: () => void;
}

export function BillingModal({ isOpen, onOpenChange, hospitalName, selectedMedicines, onSuccess }: BillingModalProps) {
  const [patientName, setPatientName] = useState("");
  const [patientCode, setPatientCode] = useState("");
  const [contactNumber, setContactNumber] = useState("");
  const [prescribedBy, setPrescribedBy] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPatientLocked, setIsPatientLocked] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Reset state on open
      setPatientName("");
      setPatientCode("");
      setContactNumber("");
      setPrescribedBy("");
      setIsGenerating(false);
      setIsPatientLocked(false);
    }
  }, [isOpen]);

  const handleGenerateBill = async () => {
    if (!patientName.trim()) return toast.error("Patient Name is required");
    if (!contactNumber.trim()) return toast.error("Contact Number is required");
    if (!prescribedBy.trim()) return toast.error("Prescribing Doctor is required");
    
    setIsGenerating(true);

    try {
      const pIdStr = patientCode.trim() ? ` (ID: ${patientCode.trim()})` : '';

      // 1. Update inventory for each selected medicine
      for (const med of selectedMedicines) {
        // med.maxQty holds the original available quantity. med.quantity is the amount sold.
        const newTotalQty = Math.max(0, med.maxQty - med.quantity);
        
        // Pass X-Hospital-ID header to satisfy backend auth requirements for DISTRICT_ADMIN
        const hospitalId = localStorage.getItem('selectedHospitalId');
        const headers: any = {
          'Content-Type': 'application/json',
          'X-Role': 'DISTRICT_ADMIN'
        };
        if (hospitalId) headers['X-Hospital-ID'] = hospitalId;
        
        const hospitalQuery = hospitalId ? `?hospital_id=${hospitalId}` : '';

        const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/inventory/${med.id}${hospitalQuery}`, {
          method: 'PUT',
          headers,
          body: JSON.stringify({ 
            quantity: newTotalQty,
            note: `Billed to patient: ${patientName}${pIdStr}`,
            patient_code: patientCode.trim() || undefined
          })
        });

        if (!res.ok) {
          throw new Error(`Failed to update inventory for ${med.name}`);
        }
      }

      // 2. Generate PDF
      const doc = new jsPDF();
      const billNo = `BILL-${Math.floor(100000 + Math.random() * 900000)}`;
      const dateStr = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
      
      // Header
      doc.setFontSize(18);
      doc.setFont("helvetica", "bold");
      doc.text(hospitalName || "Health Centre", 14, 20);
      
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text("Healthcare Centre", 14, 26);
      doc.line(14, 30, 196, 30); // Line

      // Patient Info
      doc.setFontSize(11);
      let currentY = 40;
      if (patientCode.trim()) {
        doc.text(`Patient ID: ${patientCode.trim()}`, 14, currentY);
        currentY += 6;
      }
      doc.text(`Patient Name: ${patientName}`, 14, currentY);
      currentY += 6;
      doc.text(`Contact: ${contactNumber}`, 14, currentY);
      currentY += 6;
      doc.text(`Prescribed By: ${prescribedBy}`, 14, currentY);

      // Bill Info
      doc.text(`Bill No: ${billNo}`, 140, 40);
      doc.text(`Date: ${dateStr}`, 140, 46);

      // Medicine Table
      const tableColumn = ["Medicine", "Qty", "Rate", "Amount"];
      const tableRows = selectedMedicines.map(med => [
        med.name,
        med.quantity.toString(),
        `Rs. ${med.price.toFixed(2)}`,
        `Rs. ${(med.quantity * med.price).toFixed(2)}`
      ]);

      autoTable(doc, {
        startY: currentY + 8,
        head: [tableColumn],
        body: tableRows,
        theme: 'striped',
        headStyles: { fillColor: [41, 128, 185] },
        styles: { fontSize: 10, cellPadding: 3 },
      });

      const finalY = (doc as any).lastAutoTable.finalY || 60;
      const subtotal = selectedMedicines.reduce((sum, med) => sum + (med.quantity * med.price), 0);
      
      // Total
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text(`TOTAL AMOUNT: Rs. ${subtotal.toFixed(2)}`, 140, finalY + 10);

      // Save PDF
      doc.save(`${billNo}.pdf`);
      toast.success("Bill generated successfully!");
      
      // 3. Clear state and close
      onSuccess();
      onOpenChange(false);
      
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to generate bill. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] rounded-xl border-border bg-card/95 backdrop-blur-md shadow-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-foreground">
            <FileText className="w-5 h-5 text-primary" />
            Patient Details
          </DialogTitle>
          <DialogDescription>
            Enter patient and prescription information to finalize the bill.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <label className="text-sm font-medium">Patient ID / ABHA ID</label>
            <PatientSearchInput 
              onPatientFound={(patient) => {
                setPatientCode(patient.patient_code || '');
                setPatientName(patient.name || '');
                setContactNumber(patient.contact || '');
                setIsPatientLocked(true);
              }}
              disabled={isGenerating || isPatientLocked}
            />
            {isPatientLocked && (
              <Button 
                type="button" 
                variant="ghost" 
                size="sm" 
                className="w-fit text-xs h-6 px-2 mt-1" 
                onClick={() => {
                  setIsPatientLocked(false);
                  setPatientCode('');
                  setPatientName('');
                  setContactNumber('');
                }}
              >
                Clear Patient
              </Button>
            )}
          </div>

          <div className="grid gap-2">
            <label className="text-sm font-medium">Patient Name <span className="text-destructive">*</span></label>
            <Input 
              value={patientName} 
              onChange={e => setPatientName(e.target.value)} 
              className="bg-background"
              disabled={isPatientLocked}
            />
          </div>
          
          <div className="grid gap-2">
            <label className="text-sm font-medium">Contact Number <span className="text-destructive">*</span></label>
            <Input 
              value={contactNumber} 
              onChange={e => setContactNumber(e.target.value)} 
              className="bg-background"
              disabled={isPatientLocked}
            />
          </div>
          
          <div className="grid gap-2">
            <label className="text-sm font-medium">Prescribed By <span className="text-destructive">*</span></label>
            <Input 
              placeholder="e.g. Dr. Alice Brown" 
              value={prescribedBy} 
              onChange={e => setPrescribedBy(e.target.value)} 
              className="bg-background"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0 mt-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isGenerating}>Cancel</Button>
          <Button onClick={handleGenerateBill} disabled={isGenerating} className="cursor-pointer">
            {isGenerating ? <><Loader2 className="w-4 h-4 mr-2 animate-spin"/> Processing...</> : 'Generate Bill'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
