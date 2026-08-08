"use client";
import { apiFetch } from '@/lib/api';

import { useState, useEffect } from 'react';
import { Download, FileText, Activity, AlertCircle, Calendar, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { useAuth } from '@/contexts/AuthContext';

export default function AIAuditReports() {
  const { user, selectedHospitalId } = useAuth();
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const hospitalId = 2; // Hardcoded for prototype

  const fetchReports = async () => {
    setLoading(true);
    try {
      const hospitalQuery = selectedHospitalId ? `?hospital_id=${selectedHospitalId}` : '';
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/${hospitalQuery}`);
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const generateReport = async () => {
    setGenerating(true);
    try {
      const hospitalQuery = selectedHospitalId ? `?hospital_id=${selectedHospitalId}` : '';
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/generate-pdf${hospitalQuery}`, {
        method: "POST"
      });
      if (res.ok) {
        await fetchReports();
      } else {
        console.error("Failed to generate report");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (reportId: number) => {
    try {
      const hospitalQuery = selectedHospitalId ? `?hospital_id=${selectedHospitalId}` : '';
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/${reportId}/download${hospitalQuery}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Aarogya_Audit_Report_${reportId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        console.error("Failed to download report");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto p-4 md:p-6">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-bold text-foreground">AI Operational Audits</h2>
          <p className="text-sm text-muted-foreground mt-1">Generate and review professional monthly government audit reports.</p>
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={generateReport} 
            disabled={generating}
            className="flex items-center gap-2 rounded-lg"
          >
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            {generating ? "Generating..." : "Generate Monthly Report"}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : reports.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="p-12 text-center text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No reports generated yet.</p>
            <p className="text-sm mt-1">Click the button above to run the AI audit.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {reports.map((report) => (
            <Card key={report.id} className="border-border shadow-sm overflow-hidden relative">
              <div className={`absolute left-0 top-0 bottom-0 w-2 ${
                report.risk_level === 'Critical' ? 'bg-red-500' : 
                report.risk_level === 'Moderate' ? 'bg-yellow-500' : 'bg-green-500'
              }`}></div>
              <CardContent className="p-6 pl-8 flex flex-col md:flex-row items-center justify-between gap-6">
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                      {report.month_year} Audit
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-1">
                    Monthly Operational Audit
                  </h3>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    Generated on {new Date(report.created_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex items-center gap-8 bg-muted/30 p-4 rounded-xl border border-border">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1 text-center">Health Score</p>
                    <p className={`text-2xl font-bold text-center ${
                      report.health_score >= 75 ? 'text-green-600' : 
                      report.health_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {report.health_score}
                    </p>
                  </div>
                  <div className="w-px h-10 bg-border"></div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1 text-center">Risk Level</p>
                    <div className="flex items-center gap-1">
                      {report.risk_level === 'Critical' && <AlertCircle className="w-4 h-4 text-red-500" />}
                      <span className={`font-semibold ${
                        report.risk_level === 'Critical' ? 'text-red-600' : 
                        report.risk_level === 'Moderate' ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {report.risk_level}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <Button 
                    onClick={() => handleDownload(report.id)}
                    variant="outline" 
                    className="flex items-center gap-2 border-primary/20 text-primary hover:bg-primary/10 rounded-lg cursor-pointer"
                  >
                    Download PDF
                  </Button>
                </div>

              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}




