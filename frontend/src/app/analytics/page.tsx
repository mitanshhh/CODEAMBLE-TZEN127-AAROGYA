"use client";
import { apiFetch } from '@/lib/api';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar 
} from 'recharts';
import { 
  Activity, AlertTriangle, CheckCircle, Pill, BedDouble, Users, HeartPulse, Stethoscope, AlertCircle, Loader2, Bot
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function Analytics() {
  const { selectedHospitalId } = useAuth();
  const [healthScore, setHealthScore] = useState<number | null>(null);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [dashboardMetrics, setDashboardMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(true);
  const hospitalId = selectedHospitalId;

  useEffect(() => {
    if (selectedHospitalId) {
      fetchAnalytics();
    }
  }, [selectedHospitalId]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const q = hospitalId ? `?hospital_id=${hospitalId}` : "";
      
      const [scoreRes, dashRes] = await Promise.all([
        apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/health-score${q}`),
        apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/dashboard${q}`)
      ]);
      
      if (scoreRes.ok) {
        const json = await scoreRes.json();
        setHealthScore(json.health_score ?? null);
      }
      
      if (dashRes.ok) {
        setDashboardMetrics(await dashRes.json());
      }
      
      fetchAiInsights();
    } catch (error: any) {
      console.error("Failed to load analytics", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAiInsights = async () => {
    try {
      setAiLoading(true);
      const q = hospitalId ? `?hospital_id=${hospitalId}` : "";
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/ai-insights${q}`);
      if (res.ok) {
        setAiInsights(await res.json());
      }
    } catch (error) {
      console.error("AI Fetch Error", error);
    } finally {
      setAiLoading(false);
    }
  };

  const kpis = dashboardMetrics ? {
    total_medicines: dashboardMetrics.inventory.total,
    out_of_stock: dashboardMetrics.inventory.low_stock,
    occupancy_percentage: dashboardMetrics.beds.total > 0 ? Math.round((dashboardMetrics.beds.occupied / dashboardMetrics.beds.total) * 100) : 0,
    occupied_beds: dashboardMetrics.beds.occupied,
    doctors_present: dashboardMetrics.doctors.present_today,
    total_doctors: dashboardMetrics.doctors.total,
    patient_footfall_today: dashboardMetrics.patients.total_today
  } : {
    total_medicines: 0,
    out_of_stock: 0,
    occupancy_percentage: 0,
    occupied_beds: 0,
    doctors_present: 0,
    total_doctors: 0,
    patient_footfall_today: 0
  };

  const charts = {
    footfall: dashboardMetrics?.charts?.footfall || []
  };

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center flex-col gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-muted-foreground animate-pulse font-medium">Loading Analytics...</p>
      </div>
    );
  }

  const riskLevel = healthScore !== null
    ? healthScore > 75 ? "Low Risk" : healthScore > 50 ? "Moderate" : "High Risk"
    : "Unknown";

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-foreground">AI Analytics</h2>
          <p className="text-sm text-muted-foreground mt-1 font-medium">
            Live AI-powered operational overview
          </p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Overall Status</p>
            <Badge variant="outline" className={`mt-1 font-bold px-3 py-1 text-sm ${
              riskLevel === 'Low Risk' ? 'bg-green-100 text-green-800' :
              riskLevel === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {riskLevel}
            </Badge>
          </div>
          <div className="text-right border-l pl-4 border-border/50">
            <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Health Score</p>
            <p className={`text-2xl font-black ${
              healthScore !== null && healthScore > 75 ? 'text-green-600' :
              healthScore !== null && healthScore > 50 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {healthScore !== null ? Math.round(healthScore) : '--'}<span className="text-sm text-muted-foreground font-medium">/100</span>
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Medicines</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-black text-foreground">{kpis.total_medicines}</p>
                <span className="text-xs text-red-500 font-medium">{kpis.out_of_stock} out</span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <Pill className="w-5 h-5 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Bed Occupancy</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-black text-foreground">{kpis.occupancy_percentage}%</p>
                <span className="text-xs text-muted-foreground font-medium">{kpis.occupied_beds} occupied</span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
              <BedDouble className="w-5 h-5 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Doctor Attendance</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-black text-foreground">{kpis.doctors_present}</p>
                <span className="text-xs text-muted-foreground font-medium">/ {kpis.total_doctors}</span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
              <Stethoscope className="w-5 h-5 text-indigo-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Patient Footfall</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-black text-foreground">{kpis.patient_footfall_today}</p>
                <span className="text-xs text-green-500 font-medium">Today</span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - AI Summary & Risks */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-100 shadow-sm">
            <CardHeader className="pb-3 border-b border-indigo-100/50">
              <CardTitle className="text-sm font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4" /> 
                AI Executive Summary
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100/60 border border-indigo-200 px-2 py-0.5 rounded-full">
                  <Bot className="w-3 h-3" />
                  AI Forecast
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-indigo-950 font-medium leading-relaxed">
              {aiLoading ? (
                <div className="flex items-center gap-2 text-indigo-700 animate-pulse">
                  <Loader2 className="w-4 h-4 animate-spin" /> Generating AI Insights...
                </div>
              ) : (
                aiInsights?.executive_summary || "No insights available."
              )}
            </CardContent>
          </Card>
          
          <Card className="border-border shadow-sm">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" /> 
                Risk Analysis
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                  <Bot className="w-3 h-3" />
                  AI Forecast
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {aiLoading ? (
                <div className="flex justify-center py-4"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
              ) : aiInsights?.risks ? (
                aiInsights.risks.map((risk: any, i: number) => (
                  <div key={i} className="p-3 bg-card border border-border/60 rounded-xl space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-bold uppercase text-foreground">{risk.category}</span>
                      <Badge variant="outline" className={`text-[10px] py-0 px-2 h-5 rounded-full ${risk.severity === 'High' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-yellow-50 text-yellow-700 border-yellow-200'}`}>
                        {risk.severity} Risk
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{risk.description}</p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground text-center">No risk data available.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Charts & Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Patient Footfall Trend</CardTitle>
            </CardHeader>
            <CardContent className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.footfall} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6B7280' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6B7280' }} />
                  <Tooltip cursor={{ fill: '#f3f4f6' }} contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="patients" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="border-border shadow-sm">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" /> 
                Priority Recommendations
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                  <Bot className="w-3 h-3" />
                  AI Forecast
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 grid sm:grid-cols-2 gap-3">
              {aiLoading ? (
                <div className="col-span-2 flex justify-center py-4"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
              ) : aiInsights?.recommendations?.length ? (
                aiInsights.recommendations.map((rec: string, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-muted/30 border border-border/50 rounded-xl hover:bg-muted/50 transition-colors cursor-pointer">
                    <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center shrink-0 border border-border/50 shadow-sm text-xs font-bold text-muted-foreground">
                      {i+1}
                    </div>
                    <p className="text-xs font-medium text-foreground pt-0.5">{rec}</p>
                  </div>
                ))
              ) : (
                <p className="col-span-2 text-xs text-muted-foreground text-center py-4">No recommendations available.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}





