"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format, addDays } from "date-fns";

export function AnalyticsCards({ kpis, forecast }: any) {
  if (!kpis) return null;

  const total = kpis.total_beds || 0;
  const occupied = kpis.occupied_beds || 0;
  const available = kpis.available_beds || 0;
  const maintenance = (kpis.maintenance_beds || 0) + (kpis.cleaning_beds || 0);
  const occupancyPct = kpis.occupancy_percentage || 0;

  // Process forecast data to use actual relative dates
  const actualForecast = forecast?.map((f: any) => {
    const dayNum = parseInt(f.date.replace('Day ', ''), 10) || 1;
    const realDate = addDays(new Date(), dayNum - 1);
    
    // Calculate estimated occupied/available based on current total capacity
    const estimatedOccupied = Math.round((f.occupancy / 100) * total);
    const estimatedAvailable = Math.max(0, total - estimatedOccupied - maintenance);

    return {
      ...f,
      realDate,
      dayName: format(realDate, 'EEE dd'),
      fullDate: format(realDate, 'dd MMM yyyy'),
      estimatedOccupied,
      estimatedAvailable
    };
  }) || [];

  const hasForecast = actualForecast.length > 0;
  
  let predictedAvg = 0;
  let expectedPeak = 0;
  let expectedPeakDate = "";
  
  if (hasForecast) {
    const sum = actualForecast.reduce((acc: number, curr: any) => acc + curr.occupancy, 0);
    predictedAvg = Math.round(sum / actualForecast.length);
    const peakObj = actualForecast.reduce((prev: any, current: any) => (prev.occupancy > current.occupancy) ? prev : current);
    expectedPeak = peakObj.occupancy;
    expectedPeakDate = format(peakObj.realDate, 'EEEE');
  }

  // Calculate percentages for horizontal bars
  const occWidth = total > 0 ? (occupied / total) * 100 : 0;
  const availWidth = total > 0 ? (available / total) * 100 : 0;
  const maintWidth = total > 0 ? (maintenance / total) * 100 : 0;

  return (
    <div className="space-y-6 mb-6">
      {/* KPI SECTION */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Total Beds</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-foreground">{total}</div>
            <p className="text-xs text-muted-foreground mt-1">Total capacity</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Occupied</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-blue-600">{occupied}</div>
            <p className="text-xs text-muted-foreground mt-1">Currently used</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Available</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-green-600">{available}</div>
            <p className="text-xs text-muted-foreground mt-1">Ready to use</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Maintenance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-amber-500">{maintenance}</div>
            <p className="text-xs text-muted-foreground mt-1">Unavailable</p>
          </CardContent>
        </Card>
      </div>

      {/* COMPACT METRIC */}
      <div className="flex items-center gap-2 text-sm font-medium">
        <span className="text-muted-foreground">Occupancy:</span>
        <span className={`px-2 py-0.5 rounded-md ${occupancyPct >= 85 ? 'bg-red-100 text-red-800' : occupancyPct >= 70 ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
          {occupancyPct}%
        </span>
      </div>

      {/* MAIN ANALYTICS AREA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* CARD 1: BED OCCUPANCY — NEXT 7 DAYS */}
        <Card className="bg-white border-border/50 shadow-sm flex flex-col h-[380px]">
          <CardHeader className="pb-2 shrink-0">
            <div className="flex justify-between items-start">
              <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Bed Occupancy — Next 7 Days</CardTitle>
              {hasForecast && (
                <div className="text-right flex gap-4">
                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Predicted Average</p>
                    <p className="text-sm font-semibold">{predictedAvg}%</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Expected Peak</p>
                    <p className="text-sm font-semibold">{expectedPeakDate} &middot; {expectedPeak}%</p>
                  </div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 pt-4 pb-6">
            {!hasForecast ? (
              <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                <p>Forecast data unavailable</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={actualForecast} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="dayName" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    domain={[0, 100]}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', padding: '12px' }}
                    labelFormatter={(label, entries) => {
                      if (entries && entries.length > 0) {
                        return entries[0].payload.fullDate;
                      }
                      return label;
                    }}
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white border border-border/50 shadow-md rounded-lg p-3 text-sm">
                            <p className="font-bold text-foreground mb-2">{data.fullDate}</p>
                            <div className="space-y-1">
                              <p className="flex justify-between gap-4"><span className="text-muted-foreground">Occupancy</span> <span className="font-semibold">{data.occupancy}%</span></p>
                              <p className="flex justify-between gap-4"><span className="text-muted-foreground">Occupied</span> <span className="font-semibold">{data.estimatedOccupied}</span></p>
                              <p className="flex justify-between gap-4"><span className="text-muted-foreground">Available</span> <span className="font-semibold">{data.estimatedAvailable}</span></p>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="occupancy" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    dot={{ r: 4, strokeWidth: 2, fill: "#fff" }}
                    activeDot={{ r: 6, fill: "#3b82f6" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* CARD 2: CURRENT BED STATUS */}
        <Card className="bg-white border-border/50 shadow-sm flex flex-col h-[380px]">
          <CardHeader className="pb-2 shrink-0">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Current Bed Status</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 flex flex-col justify-center gap-8 py-6">
            
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm font-medium">
                <span className="text-muted-foreground flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-blue-500 inline-block"></span>
                  Occupied
                </span>
                <span className="text-foreground font-bold">{occupied}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3">
                <div className="bg-blue-500 h-3 rounded-full transition-all duration-500" style={{ width: `${occWidth}%` }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm font-medium">
                <span className="text-muted-foreground flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-green-500 inline-block"></span>
                  Available
                </span>
                <span className="text-foreground font-bold">{available}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3">
                <div className="bg-green-500 h-3 rounded-full transition-all duration-500" style={{ width: `${availWidth}%` }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm font-medium">
                <span className="text-muted-foreground flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-amber-500 inline-block"></span>
                  Maintenance
                </span>
                <span className="text-foreground font-bold">{maintenance}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3">
                <div className="bg-amber-500 h-3 rounded-full transition-all duration-500" style={{ width: `${maintWidth}%` }}></div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-border/50 flex justify-between items-center">
              <div className="text-sm">
                <span className="text-muted-foreground">Total Beds: </span>
                <span className="font-bold">{total}</span>
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">Occupancy: </span>
                <span className="font-bold">{occupancyPct}%</span>
              </div>
            </div>

          </CardContent>
        </Card>

      </div>
    </div>
  );
}
