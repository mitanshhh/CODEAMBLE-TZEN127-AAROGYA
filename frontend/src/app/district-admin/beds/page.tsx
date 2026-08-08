"use client";
import { apiFetch } from '@/lib/api';

import { useState, useEffect } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Building2, Activity, MapPin, RefreshCw, AlertTriangle, ArrowRightLeft } from "lucide-react";
import { toast } from "sonner";

export default function DistrictBedManagement() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/beds/district/summary`);
      if (!res.ok) throw new Error("Failed to fetch district summary");
      const result = await res.json();
      setData(result);
    } catch (error) {
      console.error(error);
      toast.error("Could not fetch district data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto pb-10">
      <div className="flex justify-between items-end mb-2">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">District Capacity Monitor</h2>
          <p className="text-sm text-muted-foreground mt-1">Aggregate bed occupancy across all PHCs and CHCs.</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading} className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center border border-border/50 rounded-xl bg-white">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="bg-white border-border/50 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Total District Beds</CardTitle>
                <Building2 className="w-4 h-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-black text-foreground">{data.overall.total_beds}</div>
              </CardContent>
            </Card>

            <Card className="bg-white border-border/50 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Total Occupied</CardTitle>
                <Activity className="w-4 h-4 text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-black text-foreground">{data.overall.occupied_beds}</div>
              </CardContent>
            </Card>

            <Card className={`border-border/50 shadow-sm ${data.overall.occupancy_percentage >= 90 ? 'bg-red-50' : 'bg-white'}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">District Occupancy</CardTitle>
                <Activity className={`w-4 h-4 ${data.overall.occupancy_percentage >= 90 ? 'text-red-500' : 'text-blue-500'}`} />
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-black ${data.overall.occupancy_percentage >= 90 ? 'text-red-700' : 'text-foreground'}`}>
                  {data.overall.occupancy_percentage}%
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 border border-border/50 rounded-xl overflow-hidden bg-white shadow-sm">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Hospital</TableHead>
                    <TableHead>Occupancy</TableHead>
                    <TableHead>Available</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.hospitals.map((h: any) => (
                    <TableRow key={h.hospital_id}>
                      <TableCell className="font-semibold">
                        {h.hospital_name}
                        <div className="text-xs text-muted-foreground font-normal">{h.type}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-gray-200 rounded-full h-2 max-w-[100px]">
                            <div 
                              className={`h-2 rounded-full ${h.critical_level === 'Critical' ? 'bg-red-500' : h.critical_level === 'Moderate' ? 'bg-yellow-500' : 'bg-green-500'}`} 
                              style={{ width: `${h.occupancy_percentage}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">{h.occupancy_percentage}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{h.available_beds} beds</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          h.critical_level === 'Critical' ? 'bg-red-100 text-red-700 border-red-200' : 
                          h.critical_level === 'Moderate' ? 'bg-yellow-100 text-yellow-700 border-yellow-200' : 
                          'bg-green-100 text-green-700 border-green-200'
                        }>
                          {h.critical_level}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="outline" size="sm">View Beds</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {data.hospitals.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No hospitals found in district.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
            
            <div className="col-span-1 space-y-4">
              <Card className="bg-white border-border/50 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-orange-500" /> Action Required
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {data.hospitals.filter((h: any) => h.critical_level === 'Critical').length > 0 ? (
                    data.hospitals.filter((h: any) => h.critical_level === 'Critical').map((h: any) => (
                      <div key={h.hospital_id} className="p-3 bg-red-50 border border-red-100 rounded-lg text-sm">
                        <p className="font-bold text-red-800">{h.hospital_name} is Critical ({h.occupancy_percentage}%)</p>
                        <p className="text-red-700 mt-1 flex items-center gap-1">
                          <ArrowRightLeft className="w-3 h-3" /> {h.recommendation}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 bg-green-50 border border-green-100 rounded-lg text-sm text-green-700 font-medium flex items-center gap-2">
                      <MapPin className="w-4 h-4" /> All hospitals are operating within safe capacity limits.
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Map Preview Placeholder */}
              <Card className="bg-white border-border/50 shadow-sm overflow-hidden">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-500" /> District Map Preview
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 relative h-48 bg-blue-50">
                  <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-blue-800/60 font-medium text-sm">
                    <MapPin className="w-8 h-8 mb-2 animate-bounce" />
                    <span>Interactive Map Integration</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}


