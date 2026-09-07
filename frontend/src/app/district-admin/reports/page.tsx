"use client";
import { apiFetch } from '@/lib/api';

import { useState, useEffect } from 'react';
import { Download, FileText, AlertCircle, RefreshCw, Filter, Search, ChevronDown, CheckCircle, Map } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DistrictReportsDashboard() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/monthly`);
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

  const totalReports = reports.length;
  const avgScore = reports.length > 0 ? (reports.reduce((acc, r) => acc + r.health_score, 0) / reports.length).toFixed(1) : 0;
  const criticalCount = reports.filter(r => r.risk_level === 'Critical').length;
  
  const sortedByScore = [...reports].sort((a, b) => b.health_score - a.health_score);
  const topPHC = sortedByScore.length > 0 ? sortedByScore[0].hospital_name : "N/A";
  const bottomPHC = sortedByScore.length > 0 ? sortedByScore[sortedByScore.length - 1].hospital_name : "N/A";

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto p-4 md:p-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-foreground">District Reports Dashboard</h2>
          <p className="text-muted-foreground mt-1">Comprehensive monthly operational audit for all health centres.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2" onClick={fetchReports}>
            <RefreshCw className="w-4 h-4" />
            Refresh Data
          </Button>
          <Button className="flex items-center gap-2">
            <Map className="w-4 h-4" />
            View District Map
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Reports Generated</p>
            <p className="text-2xl font-bold text-foreground">{totalReports}</p>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <p className="text-xs text-blue-600 font-medium uppercase mb-1">Avg District Score</p>
            <p className="text-2xl font-bold text-blue-700">{avgScore}</p>
          </CardContent>
        </Card>
        
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <p className="text-xs text-red-600 font-medium uppercase mb-1">Critical Hospitals</p>
            <p className="text-2xl font-bold text-red-700">{criticalCount}</p>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4">
            <p className="text-xs text-green-600 font-medium uppercase mb-1">Top PHC</p>
            <p className="text-lg font-bold text-green-700 truncate" title={topPHC}>{topPHC}</p>
          </CardContent>
        </Card>
        
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="p-4">
            <p className="text-xs text-orange-600 font-medium uppercase mb-1">Lowest PHC</p>
            <p className="text-lg font-bold text-orange-700 truncate" title={bottomPHC}>{bottomPHC}</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Table Card */}
      <Card className="border-border shadow-sm mt-4">
        <CardHeader className="pb-4 border-b border-border flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-semibold">Monthly PHC Reports</CardTitle>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="Search hospital..." 
                className="pl-9 pr-4 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 flex justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : reports.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No reports found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
                  <tr>
                    <th className="px-6 py-4 font-medium">Hospital</th>
                    <th className="px-6 py-4 font-medium">Month</th>
                    <th className="px-6 py-4 font-medium">Score</th>
                    <th className="px-6 py-4 font-medium">Risk</th>
                    <th className="px-6 py-4 font-medium">Generated Date</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {reports.map((report) => (
                    <tr key={report.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-6 py-4 font-medium text-foreground">{report.hospital_name || `PHC #${report.hospital_id}`}</td>
                      <td className="px-6 py-4">{report.report_month}</td>
                      <td className="px-6 py-4 font-semibold">{report.health_score}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${
                          report.risk_level === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' :
                          report.risk_level === 'Moderate' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                          'bg-green-50 text-green-700 border-green-200'
                        }`}>
                          {report.risk_level}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {new Date(report.created_at).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' })}
                      </td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
                          <CheckCircle className="w-3 h-3" />
                          Generated
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          render={<a href={report.pdf_url?.startsWith('http') ? report.pdf_url : `${process.env.NEXT_PUBLIC_API_URL}${report.pdf_url}`} target="_blank" rel="noopener noreferrer" />}
                          className="text-primary hover:text-primary/80"
                        >
                          Download
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


