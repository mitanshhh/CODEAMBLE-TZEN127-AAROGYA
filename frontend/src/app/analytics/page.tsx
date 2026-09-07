"use client";

import { apiFetch } from '@/lib/api';
import { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area
} from 'recharts';
import { 
  Activity, AlertTriangle, CheckCircle, Pill, BedDouble, Users, HeartPulse, Stethoscope, FileText, Download, Loader2, Sparkles, AlertCircle, Clock, Bot
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { PeriodSelector } from "@/components/ui/PeriodSelector";
import { PeriodOption, getPeriodRange, DateRange } from "@/lib/dateUtils";
import { Progress } from "@/components/ui/progress";

export default function AnalyticsCommandCenter() {
  const { selectedHospitalId } = useAuth();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  const [metrics, setMetrics] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  
  const [period, setPeriod] = useState<PeriodOption>('This Week');
  const [dateRange, setDateRange] = useState<DateRange>(getPeriodRange('This Week'));

  useEffect(() => {
    if (selectedHospitalId) {
      fetchDashboard();
      fetchReports();
    }
  }, [selectedHospitalId, dateRange]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const q = new URLSearchParams();
      if (selectedHospitalId) q.append("hospital_id", selectedHospitalId.toString());
      if (dateRange) {
        q.append("start_date", dateRange.start.toISOString().split('T')[0]);
        q.append("end_date", dateRange.end.toISOString().split('T')[0]);
      }
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/dashboard?${q.toString()}`);
      
      if (res.ok) {
        setMetrics(await res.json());
      } else {
        toast.error("Failed to load deterministic dashboard metrics");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error loading analytics.");
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    if (!selectedHospitalId) return;
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/reports?hospital_id=${selectedHospitalId}`);
      if (res.ok) {
        setReports(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch reports", err);
    }
  };

  const generateReport = async () => {
    if (!metrics || !selectedHospitalId) return;
    
    setGenerating(true);
    const toastId = toast.loading("Synthesizing AI Operations Report...");
    
    try {
      const payload = {
        data_version: metrics.data_version,
        period_type: period,
        period_start: dateRange.start.toISOString(),
        period_end: dateRange.end.toISOString(),
        analytics_data: metrics
      };
      
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/generate-ai?hospital_id=${selectedHospitalId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        toast.success("AI Analysis generated successfully!", { id: toastId });
        fetchReports(); // Refresh history
      } else {
        toast.error("AI Generation failed.", { id: toastId });
      }
    } catch (err) {
      console.error(err);
      toast.error("Error generating AI report.", { id: toastId });
    } finally {
      setGenerating(false);
    }
  };

  // The latest report matching current selected period
  const latestReport = useMemo(() => {
    return reports.find(r => r.period_type === period) || null;
  }, [reports, period]);

  // Check if latest report matches the current deterministic data payload
  const isDataStale = latestReport ? latestReport.data_version !== metrics?.data_version : true;

  if (loading && !metrics) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="font-medium animate-pulse">Aggregating Deterministic Data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20 fade-in">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <Activity className="h-8 w-8 text-blue-600" />
            Operations Command Center
          </h1>
          <p className="text-slate-500 mt-1">Deterministic Health & Capacity Overview</p>
        </div>
        
        <div className="flex items-center gap-4 bg-white p-2 rounded-xl border shadow-sm">
          <PeriodSelector 
            value={period} 
            onChange={(p) => {
              setPeriod(p);
              setDateRange(getPeriodRange(p));
            }} 
          />
        </div>
      </div>

      {/* HEALTH SCORE HERO */}
      <Card className="bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600 border-none text-white shadow-xl overflow-hidden relative">
        <div className="absolute right-0 top-0 opacity-10 pointer-events-none">
          <HeartPulse className="w-96 h-96 -mt-20 -mr-20" />
        </div>
        <CardContent className="p-8 flex flex-col md:flex-row items-center gap-12 relative z-10">
          <div className="flex-shrink-0 flex flex-col items-center justify-center p-8 bg-white/10 rounded-full border border-white/20 shadow-inner backdrop-blur-md">
            <div className="text-6xl font-black tabular-nums tracking-tighter text-white">
              {metrics?.health_score ?? 0}
            </div>
            <div className="text-blue-100 font-semibold uppercase tracking-widest text-sm mt-2">Overall Health</div>
          </div>
          
          <div className="flex-1 space-y-6 w-full">
            <h3 className="text-2xl font-semibold text-white">System Vital Signs</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-blue-100 flex items-center gap-2"><BedDouble className="h-4 w-4"/> Bed Availability</span>
                  <span className="font-medium text-white">{100 - (metrics?.beds.occupancy_pct || 0)}%</span>
                </div>
                <Progress value={100 - (metrics?.beds.occupancy_pct || 0)} className="h-2 bg-blue-900/50" indicatorClassName="bg-white" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-blue-100 flex items-center gap-2"><Users className="h-4 w-4"/> Doctor Attendance</span>
                  <span className="font-medium text-white">{metrics?.doctors.attendance_today_pct || 0}%</span>
                </div>
                <Progress value={metrics?.doctors.attendance_today_pct || 0} className="h-2 bg-blue-900/50" indicatorClassName="bg-white" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-blue-100 flex items-center gap-2"><Pill className="h-4 w-4"/> Inventory Stock</span>
                  <span className="font-medium text-white">
                    {metrics?.inventory.total > 0 ? Math.round(((metrics?.inventory.total - metrics?.inventory.low_stock - metrics?.inventory.out_of_stock) / metrics?.inventory.total) * 100) : 0}%
                  </span>
                </div>
                <Progress value={metrics?.inventory.total > 0 ? Math.round(((metrics?.inventory.total - metrics?.inventory.low_stock - metrics?.inventory.out_of_stock) / metrics?.inventory.total) * 100) : 0} className="h-2 bg-blue-900/50" indicatorClassName="bg-white" />
              </div>
              
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 4-COLUMN DETERMINISTIC DASHBOARD */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* PATIENTS */}
        <Card className="hover:shadow-lg transition-all border-t-4 border-t-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 flex justify-between items-center uppercase tracking-wider">
              Patients <Users className="h-4 w-4 text-blue-500"/>
            </CardTitle>
            <div className="text-3xl font-bold">{metrics?.patients.total_period || 0}</div>
            <CardDescription>Visits in period</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-24 mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics?.patients.trend || []}>
                  <defs>
                    <linearGradient id="colorPatients" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}/>
                  <Area type="monotone" dataKey="patients" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorPatients)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between mt-4 text-xs font-medium text-slate-600 bg-slate-50 p-2 rounded-md">
              <div className="flex flex-col items-center"><span>{metrics?.patients.admitted}</span><span className="text-slate-400">Adm</span></div>
              <div className="flex flex-col items-center"><span>{metrics?.patients.outpatient}</span><span className="text-slate-400">Wait</span></div>
              <div className="flex flex-col items-center"><span>{metrics?.patients.discharged}</span><span className="text-slate-400">Dis</span></div>
            </div>
          </CardContent>
        </Card>

        {/* BEDS */}
        <Card className="hover:shadow-lg transition-all border-t-4 border-t-indigo-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 flex justify-between items-center uppercase tracking-wider">
              Beds <BedDouble className="h-4 w-4 text-indigo-500"/>
            </CardTitle>
            <div className="text-3xl font-bold">{metrics?.beds.occupied || 0} <span className="text-lg font-normal text-slate-400">/ {metrics?.beds.total}</span></div>
            <CardDescription>Currently Occupied</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-24 mt-4 flex items-end">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Occupied', val: metrics?.beds.occupied, fill: '#6366f1' },
                  { name: 'Available', val: metrics?.beds.available, fill: '#e2e8f0' },
                  { name: 'Maintenance', val: metrics?.beds.maintenance, fill: '#f87171' }
                ]}>
                  <Tooltip cursor={{fill: 'transparent'}}/>
                  <Bar dataKey="val" radius={[4, 4, 0, 0]} barSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between mt-4 text-xs font-medium text-slate-600 bg-slate-50 p-2 rounded-md">
              <div className="flex flex-col items-center"><span className="text-indigo-600">{metrics?.beds.occupancy_pct}%</span><span className="text-slate-400">Occupancy</span></div>
              <div className="flex flex-col items-center"><span className="text-green-600">{metrics?.beds.available}</span><span className="text-slate-400">Avail</span></div>
            </div>
          </CardContent>
        </Card>

        {/* DOCTORS */}
        <Card className="hover:shadow-lg transition-all border-t-4 border-t-teal-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 flex justify-between items-center uppercase tracking-wider">
              Doctors <Stethoscope className="h-4 w-4 text-teal-500"/>
            </CardTitle>
            <div className="text-3xl font-bold">{metrics?.doctors.present_today || 0} <span className="text-lg font-normal text-slate-400">/ {metrics?.doctors.total}</span></div>
            <CardDescription>Present Today</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-24 mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics?.doctors.trend || []}>
                  <Tooltip />
                  <Line type="stepAfter" dataKey="present" stroke="#14b8a6" strokeWidth={3} dot={{r:4, fill:"#14b8a6"}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 text-xs font-medium text-slate-600 bg-slate-50 p-2 rounded-md text-center">
              <span className="text-teal-600">{metrics?.doctors.attendance_today_pct}%</span> <span className="text-slate-400">Avg Attendance Rate</span>
            </div>
          </CardContent>
        </Card>

        {/* INVENTORY */}
        <Card className="hover:shadow-lg transition-all border-t-4 border-t-rose-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 flex justify-between items-center uppercase tracking-wider">
              Inventory <Pill className="h-4 w-4 text-rose-500"/>
            </CardTitle>
            <div className="text-3xl font-bold text-rose-600">{metrics?.inventory.low_stock + metrics?.inventory.out_of_stock || 0}</div>
            <CardDescription>Items need attention</CardDescription>
          </CardHeader>
          <CardContent>
             <div className="mt-4 space-y-2 h-24 overflow-y-auto pr-2 custom-scrollbar">
               {metrics?.inventory.critical_items?.length > 0 ? (
                 metrics.inventory.critical_items.map((item: any, i: number) => (
                   <div key={i} className="flex justify-between items-center text-xs p-2 bg-rose-50 rounded text-rose-900 border border-rose-100">
                     <span className="font-semibold truncate max-w-[100px]">{item.name}</span>
                     <span className="tabular-nums font-bold">{item.quantity} left</span>
                   </div>
                 ))
               ) : (
                 <div className="flex h-full items-center justify-center text-xs text-slate-400 italic">No critical items.</div>
               )}
             </div>
             <div className="flex justify-between mt-4 text-xs font-medium text-slate-600 bg-slate-50 p-2 rounded-md">
              <div className="flex flex-col items-center"><span>{metrics?.inventory.total}</span><span className="text-slate-400">Total Items</span></div>
              <div className="flex flex-col items-center"><span className="text-rose-600">{metrics?.inventory.out_of_stock}</span><span className="text-slate-400">OOS</span></div>
            </div>
          </CardContent>
        </Card>

      </div>

      {/* AI COMMAND CENTER */}
      <Card className="border-slate-200 shadow-md">
        <CardHeader className="bg-slate-50/50 border-b pb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-500" />
                AI Operations Synthesis
              </CardTitle>
              <CardDescription className="mt-1">
                Deep analysis of deterministic data using Gemini 2.5 Flash
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-3">
              {isDataStale && latestReport && (
                 <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 py-1">
                   <Clock className="w-3 h-3 mr-1"/> Data updated since last run
                 </Badge>
              )}
              
              {latestReport && !isDataStale && latestReport.pdf_url && (
                <Button variant="outline" className="gap-2" onClick={() => window.open(latestReport.pdf_url.startsWith('http') ? latestReport.pdf_url : `${process.env.NEXT_PUBLIC_API_URL}${latestReport.pdf_url}`)}>
                  <Download className="h-4 w-4" /> Export PDF
                </Button>
              )}
              
              <Button 
                onClick={generateReport} 
                disabled={generating || (!isDataStale && latestReport)}
                className="bg-blue-600 hover:bg-blue-700 shadow-md gap-2"
              >
                {generating ? (
                  <><Loader2 className="w-4 h-4 animate-spin"/> Synthesizing...</>
                ) : (
                  (!isDataStale && latestReport) ? <><CheckCircle className="w-4 h-4"/> Up to Date</> : <><Sparkles className="w-4 h-4"/> Generate Analysis</>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {latestReport ? (
             <div className="divide-y">
                <div className="p-6 bg-blue-50/50">
                  <h4 className="text-sm font-bold text-blue-900 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <FileText className="w-4 h-4"/> Executive Summary
                  </h4>
                  <p className="text-slate-700 leading-relaxed">
                    {latestReport.executive_summary}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x">
                  <div className="p-6">
                     <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-600"/> Key Insights
                     </h4>
                     <ul className="space-y-3">
                       {(() => {
                         try {
                           const insights = JSON.parse(latestReport.key_insights);
                           return insights.map((insight: string, idx: number) => (
                             <li key={idx} className="flex gap-3 text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border">
                               <div className="mt-0.5"><CheckCircle className="w-4 h-4 text-blue-500"/></div>
                               <span>{insight}</span>
                             </li>
                           ));
                         } catch (e) { return <li className="text-sm text-slate-500">Failed to load insights.</li>; }
                       })()}
                     </ul>
                  </div>

                  <div className="p-6 space-y-6">
                     <div>
                       <h4 className="text-sm font-bold text-rose-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-rose-600"/> Detected Risks
                       </h4>
                       <div className="space-y-3">
                         {(() => {
                           try {
                             const risks = JSON.parse(latestReport.risk_analysis);
                             if (risks.length === 0) return <p className="text-sm text-slate-500">No risks detected.</p>;
                             return risks.map((r: any, idx: number) => (
                               <div key={idx} className="p-3 bg-rose-50 border border-rose-100 rounded-lg text-sm">
                                 <div className="flex justify-between items-center mb-1">
                                   <span className="font-bold text-rose-900">{r.category || 'Risk'}</span>
                                   <Badge variant="outline" className="bg-white text-rose-700 border-rose-200">{r.severity}</Badge>
                                 </div>
                                 <p className="text-rose-800/80">{r.description}</p>
                               </div>
                             ));
                           } catch (e) { return <p className="text-sm text-slate-500">Failed to load risks.</p>; }
                         })()}
                       </div>
                     </div>
                     
                     <div>
                       <h4 className="text-sm font-bold text-emerald-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-emerald-600"/> Strategic Recommendations
                       </h4>
                       <ul className="space-y-2">
                         {(() => {
                           try {
                             const recs = JSON.parse(latestReport.recommendations);
                             return recs.map((rec: string, idx: number) => (
                               <li key={idx} className="flex gap-3 text-sm text-emerald-900 bg-emerald-50/50 p-2 rounded">
                                 <div className="mt-0.5 text-emerald-500">•</div>
                                 <span>{rec}</span>
                               </li>
                             ));
                           } catch (e) { return <li className="text-sm text-slate-500">Failed to load recommendations.</li>; }
                         })()}
                       </ul>
                     </div>
                  </div>
                </div>
             </div>
          ) : (
            <div className="p-16 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4 text-blue-600">
                <Bot className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-800">No AI Report Generated for this Period</h3>
              <p className="text-slate-500 max-w-md mt-2">
                Generate an AI analysis to interpret the deterministic data, identify operational risks, and receive actionable recommendations.
              </p>
              <Button onClick={generateReport} className="mt-6 gap-2" size="lg">
                <Sparkles className="w-4 h-4"/> Generate Now
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* REPORT HISTORY */}
      {reports.length > 0 && (
        <Card className="border-none shadow-sm bg-slate-50">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-700">Past Analyses History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-200/50">
                  <tr>
                    <th className="px-4 py-3 rounded-tl-lg">Date Generated</th>
                    <th className="px-4 py-3">Period Type</th>
                    <th className="px-4 py-3">Health Score</th>
                    <th className="px-4 py-3">Hash Version</th>
                    <th className="px-4 py-3 rounded-tr-lg">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r, idx) => (
                    <tr key={idx} className="border-b border-slate-200 last:border-0 hover:bg-white transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-900">
                        {new Date(r.generated_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{r.period_type}</td>
                      <td className="px-4 py-3 font-bold text-blue-600">{r.health_score}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">{r.data_version.substring(0, 8)}...</td>
                      <td className="px-4 py-3">
                        <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                                onClick={() => r.pdf_url ? window.open(r.pdf_url.startsWith('http') ? r.pdf_url : `${process.env.NEXT_PUBLIC_API_URL}${r.pdf_url}`) : toast.error("PDF not available")}>
                          View PDF
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

    </div>
  );
}
