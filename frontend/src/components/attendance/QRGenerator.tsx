"use client";

import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api';
import { QRCodeSVG } from 'qrcode.react';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { QrCode, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export default function QRGenerator() {
  const [qrToken, setQrToken] = useState("");
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);


  const fetchToken = async (lat?: number, lng?: number) => {
    try {
      const authToken = localStorage.getItem("token") || "mock_token";
      const role = localStorage.getItem("role") || "MEDICAL_OFFICER";
      
      const body = lat && lng ? JSON.stringify({ lat, lng }) : undefined;
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/attendance/qr/generate`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${authToken}`, 
          'X-Role': role,
          'Content-Type': 'application/json'
        },
        body
      });
      if (res.ok) {
        const data = await res.json();
        // Backend returns qr_token (DailyQRSessionResponse schema)
        setQrToken(data.qr_token);
        setGeneratedAt(new Date());
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Failed to generate QR");
      }
    } catch (e) {
      toast.error("Network error");
    } finally {
      setLoading(false);
    }
  };

  const generateQR = async () => {
    setLoading(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => fetchToken(pos.coords.latitude, pos.coords.longitude),
        (err) => {
          console.warn("Geolocation error:", err);
          toast.error("Could not get location. Falling back to default.");
          fetchToken();
        },
        { enableHighAccuracy: false, timeout: 15000, maximumAge: 0 }
      );
    } else {
      fetchToken();
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (open) {
      if (!token) generateQR();
      // Regenerate QR every 4.5 minutes (270,000 ms) to keep it fresh
      interval = setInterval(generateQR, 270000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [open]);

  const handleOpen = (isOpen: boolean) => {
    setOpen(isOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger render={<Button className="flex items-center gap-2 cursor-pointer shadow-md" />}>
        <QrCode className="w-4 h-4" />
        Show Daily Attendance QR
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle className="text-center">Daily Attendance QR Code</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col items-center justify-center py-6 gap-6">
          {loading ? (
            <div className="w-48 h-48 flex items-center justify-center border-2 border-dashed border-border rounded-xl">
              <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : qrToken ? (
            <div className="p-4 bg-white rounded-xl shadow-sm border border-border">
              <QRCodeSVG value={qrToken} size={256} level="L" includeMargin={true} />
            </div>
          ) : (
            <div className="w-48 h-48 flex items-center justify-center border-2 border-dashed border-border rounded-xl text-muted-foreground">
              Failed to load
            </div>
          )}
          
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">Have doctors scan this to mark attendance.</p>
            {generatedAt && (
              <p className="text-xs text-muted-foreground mt-1">
                Generated at {generatedAt.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })} · Valid for 5 minutes
              </p>
            )}
          </div>
          
          <Button onClick={generateQR} variant="outline" className="w-full flex items-center gap-2 cursor-pointer">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Regenerate QR Code
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

