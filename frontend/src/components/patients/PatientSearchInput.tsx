import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, AlertCircle, Search } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';

interface PatientSearchInputProps {
  onPatientFound: (patient: any) => void;
  disabled?: boolean;
}

export function PatientSearchInput({ onPatientFound, disabled }: PatientSearchInputProps) {
  const [patientCode, setPatientCode] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleCheck = async () => {
    if (!patientCode.trim()) {
      toast.error('Please enter a Patient ID / ABHA ID');
      return;
    }

    setIsChecking(true);
    setStatus('idle');

    try {
      const hospitalId = localStorage.getItem('selectedHospitalId');
      const headers: any = {
        'Content-Type': 'application/json',
      };
      if (hospitalId) headers['X-Hospital-ID'] = hospitalId;
      const hospitalQuery = hospitalId ? `?hospital_id=${hospitalId}` : '';

      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/patients/code/${patientCode.trim()}${hospitalQuery}`, {
        headers
      });

      if (!res.ok) {
        setStatus('error');
        toast.error('Patient not found. Please check the ID.');
        setIsChecking(false);
        return;
      }

      const data = await res.json();
      setStatus('success');
      toast.success('Patient found!');
      onPatientFound(data);
    } catch (err: any) {
      setStatus('error');
      toast.error('An error occurred while searching. Please try again.');
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="flex gap-2 items-center">
      <div className="relative flex-1">
        <Input
          placeholder="Enter Patient ID / ABHA ID"
          value={patientCode}
          onChange={(e) => {
            setPatientCode(e.target.value);
            setStatus('idle');
          }}
          disabled={isChecking}
          className={`pr-10 ${status === 'success' ? 'border-green-500 focus-visible:ring-green-500' : status === 'error' ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
        />
        {status === 'success' && (
          <CheckCircle2 className="absolute right-3 top-2.5 h-5 w-5 text-green-500" />
        )}
        {status === 'error' && (
          <AlertCircle className="absolute right-3 top-2.5 h-5 w-5 text-red-500" />
        )}
      </div>
      <Button 
        type="button" 
        variant="secondary" 
        onClick={handleCheck} 
        disabled={isChecking || !patientCode.trim()}
      >
        {isChecking ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
        Check
      </Button>
    </div>
  );
}
