"use client";
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Clock, Activity, AlertTriangle, CalendarDays, ChevronDown, Check } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts';
import {
  eachDayOfInterval, startOfDay, endOfDay,
  isSameDay, startOfWeek, endOfWeek,
  subDays, startOfMonth, endOfMonth, subMonths,
  format, isWithinInterval, startOfYear, endOfYear, eachMonthOfInterval,
  isAfter, parseISO
} from 'date-fns';

// ── Status config for Patient Flow chart ─────────────────────────────────────
const OUTCOME_CONFIG = [
  { status: 'Outpatient',  label: 'Outpatient',  color: '#3b82f6', bg: 'bg-blue-500'    },
  { status: 'Admitted',    label: 'Admitted',     color: '#f59e0b', bg: 'bg-amber-500'   },
  { status: 'Discharged',  label: 'Discharged',   color: '#10b981', bg: 'bg-emerald-500' },
  { status: 'Emergency',   label: 'Emergency',    color: '#ef4444', bg: 'bg-red-500'     },
  { status: 'Referred',    label: 'Referred',     color: '#8b5cf6', bg: 'bg-violet-500'  },
];

// ── Extended period type ──────────────────────────────────────────────────────
type ExtendedPeriod = 'Today' | 'This Week' | 'This Month' | 'Previous Month' | 'This Year' | 'Custom';

interface ResolvedRange { start: Date; end: Date; customStart?: string; customEnd?: string; }

// ── Resolve date range ────────────────────────────────────────────────────────
function resolveDateRange(period: ExtendedPeriod, customStart?: string, customEnd?: string): { start: Date; end: Date } {
  const now = new Date();
  const WEEK = { weekStartsOn: 1 as const };
  switch (period) {
    case 'Today':          return { start: startOfDay(now), end: endOfDay(now) };
    case 'This Week':      return { start: startOfWeek(now, WEEK), end: endOfWeek(now, WEEK) };
    case 'This Month':     return { start: startOfMonth(now), end: endOfMonth(now) };
    case 'Previous Month': { const pm = subMonths(now, 1); return { start: startOfMonth(pm), end: endOfMonth(pm) }; }
    case 'This Year':      return { start: startOfYear(now), end: endOfYear(now) };
    case 'Custom': {
      if (customStart && customEnd) {
        const s = startOfDay(new Date(customStart));
        const e = endOfDay(new Date(customEnd));
        return { start: s, end: e > now ? endOfDay(now) : e };
      }
      return { start: startOfWeek(now, WEEK), end: endOfWeek(now, WEEK) };
    }
    default: return { start: startOfWeek(now, WEEK), end: endOfWeek(now, WEEK) };
  }
}

// ── Chart Period Picker ───────────────────────────────────────────────────────
const PERIOD_OPTIONS: { value: ExtendedPeriod; label: string; desc: string }[] = [
  { value: 'Today',         label: 'Today',          desc: 'Current day activity'    },
  { value: 'This Week',     label: 'This Week',       desc: 'Mon – Sun (current)'    },
  { value: 'This Month',    label: 'This Month',      desc: format(new Date(), 'MMMM yyyy') },
  { value: 'Previous Month',label: 'Previous Month',  desc: format(subMonths(new Date(), 1), 'MMMM yyyy') },
  { value: 'This Year',     label: 'Whole Year',      desc: format(new Date(), 'yyyy') },
  { value: 'Custom',        label: 'Custom Range',    desc: 'Pick start & end date'  },
];

function ChartPeriodPicker({
  value, onChange, customStart, customEnd, onCustomChange
}: {
  value: ExtendedPeriod;
  onChange: (v: ExtendedPeriod) => void;
  customStart?: string;
  customEnd?: string;
  onCustomChange?: (start: string, end: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});
  const btnRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const today = format(new Date(), 'yyyy-MM-dd');

  // Calculate fixed position from trigger button
  const openDropdown = () => {
    if (!btnRef.current) return;
    const r = btnRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - r.bottom;
    const panelH = 380; // approximate max height
    const top = spaceBelow < panelH && r.top > panelH
      ? r.top - panelH - 4  // open upward
      : r.bottom + 4;        // open downward
    setDropdownStyle({
      position: 'fixed',
      top,
      right: window.innerWidth - r.right,
      width: 256,
      zIndex: 9999,
    });
    setOpen(o => !o);
  };

  useEffect(() => {
    function handleClose(e: MouseEvent) {
      if (
        panelRef.current && !panelRef.current.contains(e.target as Node) &&
        btnRef.current && !btnRef.current.contains(e.target as Node)
      ) setOpen(false);
    }
    function handleScroll() {
      // Don't close if a date input inside the panel is focused (native calendar is open)
      const active = document.activeElement;
      if (panelRef.current && active && panelRef.current.contains(active)) return;
      setOpen(false);
    }
    document.addEventListener('mousedown', handleClose);
    window.addEventListener('scroll', handleScroll, true); // capture phase catches all scroll events
    return () => {
      document.removeEventListener('mousedown', handleClose);
      window.removeEventListener('scroll', handleScroll, true);
    };
  }, []);

  const selected = PERIOD_OPTIONS.find(o => o.value === value);

  return (
    <>
      {/* Trigger button */}
      <button
        ref={btnRef}
        onClick={openDropdown}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-muted/30 hover:bg-muted/60 text-sm font-medium text-foreground transition-all cursor-pointer shadow-sm shrink-0"
      >
        <CalendarDays className="w-3.5 h-3.5 text-blue-500" />
        <span>{selected?.label ?? 'Select Period'}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-muted-foreground transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Fixed dropdown panel — escapes all overflow:hidden parents */}
      {open && (
        <div
          ref={panelRef}
          style={dropdownStyle}
          className="bg-card border border-border rounded-xl shadow-2xl overflow-y-auto max-h-[min(400px,80vh)] animate-in fade-in slide-in-from-top-2 duration-150"
        >
          <div className="p-1.5">
            {PERIOD_OPTIONS.filter(o => o.value !== 'Custom').map((opt) => (
              <button
                key={opt.value}
                onClick={() => { onChange(opt.value); setOpen(false); }}
                className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg text-left transition-colors cursor-pointer ${
                  value === opt.value ? 'bg-primary/10 text-primary' : 'hover:bg-muted/60 text-foreground'
                }`}
              >
                <div>
                  <p className="text-sm font-medium leading-tight">{opt.label}</p>
                  <p className={`text-xs mt-0.5 ${value === opt.value ? 'text-primary/70' : 'text-muted-foreground'}`}>{opt.desc}</p>
                </div>
                {value === opt.value && <Check className="w-4 h-4 text-primary shrink-0" />}
              </button>
            ))}

            {/* Divider */}
            <div className="h-px bg-border/60 my-1.5 mx-2" />

            {/* Custom range */}
            <button
              onClick={() => onChange('Custom')}
              className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg text-left transition-colors cursor-pointer ${
                value === 'Custom' ? 'bg-primary/10 text-primary' : 'hover:bg-muted/60 text-foreground'
              }`}
            >
              <div>
                <p className="text-sm font-medium">Custom Range</p>
                <p className={`text-xs mt-0.5 ${value === 'Custom' ? 'text-primary/70' : 'text-muted-foreground'}`}>Pick start &amp; end date</p>
              </div>
              {value === 'Custom' && <Check className="w-4 h-4 text-primary shrink-0" />}
            </button>

            {value === 'Custom' && (
              <div className="px-3 pb-3 pt-1.5 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-muted-foreground font-medium mb-1 block">From</label>
                    <input
                      type="date"
                      max={customEnd || today}
                      value={customStart || ''}
                      onChange={e => onCustomChange?.(e.target.value, customEnd || today)}
                      className="w-full text-xs border border-border rounded-md px-2 py-1.5 bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground font-medium mb-1 block">To</label>
                    <input
                      type="date"
                      min={customStart || undefined}
                      max={today}
                      value={customEnd || today}
                      onChange={e => onCustomChange?.(customStart || format(subDays(new Date(), 7), 'yyyy-MM-dd'), e.target.value)}
                      className="w-full text-xs border border-border rounded-md px-2 py-1.5 bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                    />
                  </div>
                </div>
                {customStart && customEnd && (
                  <button
                    onClick={() => setOpen(false)}
                    className="w-full text-xs bg-primary text-primary-foreground rounded-md py-1.5 font-semibold hover:bg-primary/90 transition-colors cursor-pointer"
                  >
                    Apply Range
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}


// ── Custom Tooltip ────────────────────────────────────────────────────────────
function VolumeTooltip({ active, payload }: any) {
  if (!active || !payload?.length || payload[0]?.value == null) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-card border border-border rounded-lg p-3 shadow-lg text-sm min-w-[150px]">
      <p className="font-semibold text-foreground">{d.label}</p>
      {d.fullDate && <p className="text-muted-foreground text-xs mb-2">{d.fullDate}</p>}
      <div className="flex items-center gap-2 mt-1">
        <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
        <span className="text-muted-foreground text-xs">Patient Visits</span>
        <span className="font-bold text-foreground ml-auto">{payload[0].value}</span>
      </div>
    </div>
  );
}

// ── Patient Volume Trend ──────────────────────────────────────────────────────
function PatientVolumeTrend({ patients }: { patients: any[] }) {
  const [period, setPeriod] = useState<ExtendedPeriod>('This Week');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const chartData = useMemo(() => {
    const { start, end } = resolveDateRange(period, customStart, customEnd);
    const now = new Date();

    if (period === 'Today') {
      return Array.from({ length: 24 }, (_, h) => {
        const bStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h);
        const bEnd   = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, 59, 59);
        if (bStart > now) return { label: `${h}:00`, fullDate: format(bStart, 'hh:mm a'), count: null };
        const count = patients.filter(p => {
          const d = new Date(p.admitted_at);
          return d >= bStart && d <= bEnd;
        }).length;
        return { label: `${h}:00`, fullDate: format(bStart, 'hh:mm a'), count };
      });
    }

    // Year view → monthly buckets
    if (period === 'This Year') {
      const months = eachMonthOfInterval({ start, end });
      return months.map(month => {
        const mEnd = endOfMonth(month);
        const isFuture = month > now && !isSameDay(month, now);
        if (isFuture) return { label: format(month, 'MMM'), fullDate: format(month, 'MMM yyyy'), count: null };
        const count = patients.filter(p =>
          isWithinInterval(new Date(p.admitted_at), { start: startOfDay(month), end: mEnd > now ? endOfDay(now) : mEnd })
        ).length;
        return { label: format(month, 'MMM'), fullDate: format(month, 'MMM yyyy'), count };
      });
    }

    const days = eachDayOfInterval({ start, end });
    return days.map(day => {
      const isLongView = period === 'This Month' || period === 'Previous Month' || period === 'Custom';
      const label = format(day, isLongView ? 'dd' : 'EEE');
      const isFuture = day > now && !isSameDay(day, now);
      if (isFuture) return { label, fullDate: format(day, 'dd MMM yyyy'), count: null };
      const count = patients.filter(p =>
        isWithinInterval(new Date(p.admitted_at), { start: startOfDay(day), end: endOfDay(day) })
      ).length;
      return { label, fullDate: format(day, 'dd MMM yyyy'), count };
    });
  }, [patients, period, customStart, customEnd]);

  const hasData = chartData.some(d => d.count !== null && (d.count as number) > 0);

  return (
    <Card className="bg-card border-border shadow-sm flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="text-base font-bold">Patient Volume Trend</CardTitle>
          <ChartPeriodPicker
            value={period}
            onChange={setPeriod}
            customStart={customStart}
            customEnd={customEnd}
            onCustomChange={(s, e) => { setCustomStart(s); setCustomEnd(e); }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">Daily patient registrations over time</p>
      </CardHeader>
      <CardContent className="h-[260px]">
        {!hasData ? (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-2">
            <Activity className="w-8 h-8 opacity-30" />
            <p className="text-sm">No patient activity recorded for this period.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis
                dataKey="label"
                stroke="hsl(var(--muted-foreground))"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                interval={
                  period === 'Today'
                    ? 3
                    : period === 'This Month' || period === 'Previous Month'
                    ? 4
                    : period === 'This Year'
                    ? 0
                    : period === 'Custom' && chartData.length > 14
                    ? Math.floor(chartData.length / 7)
                    : 0
                }
              />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip content={<VolumeTooltip />} />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2.5}
                fill="url(#volGrad)"
                dot={{ r: 3, fill: '#3b82f6', strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

// ── Patient Flow / Outcome ────────────────────────────────────────────────────
function PatientFlowOutcome({ patients }: { patients: any[] }) {
  const [period, setPeriod] = useState<ExtendedPeriod>('This Week');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const { rows, total } = useMemo(() => {
    const { start, end } = resolveDateRange(period, customStart, customEnd);
    const inRange = patients.filter(p =>
      isWithinInterval(new Date(p.admitted_at), { start, end })
    );
    const total = inRange.length;
    if (total === 0) return { rows: [], total: 0 };

    const counts: Record<string, number> = {};
    inRange.forEach(p => { const s = p.status || 'Outpatient'; counts[s] = (counts[s] || 0) + 1; });

    const rows = OUTCOME_CONFIG
      .map(cfg => ({ ...cfg, count: counts[cfg.status] || 0, pct: Math.round(((counts[cfg.status] || 0) / total) * 100) }))
      .filter(r => r.count > 0)
      .sort((a, b) => b.count - a.count);

    Object.keys(counts).forEach(s => {
      if (!OUTCOME_CONFIG.find(c => c.status === s)) {
        rows.push({ status: s, label: s, color: '#6b7280', bg: 'bg-gray-500', count: counts[s], pct: Math.round((counts[s] / total) * 100) });
      }
    });

    return { rows, total };
  }, [patients, period, customStart, customEnd]);

  return (
    <Card className="bg-card border-border shadow-sm flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="text-base font-bold">Patient Flow / Outcome</CardTitle>
          <ChartPeriodPicker
            value={period}
            onChange={setPeriod}
            customStart={customStart}
            customEnd={customEnd}
            onCustomChange={(s, e) => { setCustomStart(s); setCustomEnd(e); }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">Distribution of patient outcomes by current status</p>
      </CardHeader>
      <CardContent className="flex-1">
        {rows.length === 0 ? (
          <div className="h-[220px] flex flex-col items-center justify-center text-muted-foreground gap-2">
            <Activity className="w-8 h-8 opacity-30" />
            <p className="text-sm">No patient outcome data available.</p>
          </div>
        ) : (
          <div className="space-y-3 mt-2">
            {rows.map(row => (
              <div key={row.status} className="flex items-center gap-3">
                <div className="w-24 shrink-0 flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${row.bg}`} aria-hidden />
                  <span className="text-sm font-medium text-foreground truncate">{row.label}</span>
                </div>
                <div className="flex-1 h-5 bg-muted/40 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${row.pct}%`, backgroundColor: row.color }}
                    role="progressbar"
                    aria-valuenow={row.pct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`${row.label}: ${row.pct}%`}
                  />
                </div>
                <div className="shrink-0 flex items-center gap-2 min-w-[64px] justify-end">
                  <span className="text-sm font-bold text-foreground">{row.count}</span>
                  <span className="text-xs text-muted-foreground w-9 text-right">{row.pct}%</span>
                </div>
              </div>
            ))}
            <div className="pt-3 mt-1 border-t border-border/60 flex items-center justify-between">
              <span className="text-xs text-muted-foreground font-medium">Total patient encounters</span>
              <span className="text-sm font-bold text-foreground">{total}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────
export function PatientAnalyticsCards({ kpis, charts, patients = [] }: any) {
  if (!kpis) return null;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* KPI Cards — unchanged */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Today's Footfall</CardTitle>
            <Users className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-foreground">{kpis.total_today}</div>
            <p className="text-xs font-medium text-muted-foreground mt-1">Registered today</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Avg Wait Time</CardTitle>
            <Clock className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-foreground">{kpis.avg_wait_time_mins} <span className="text-lg text-muted-foreground">min</span></div>
            <p className="text-xs font-medium text-muted-foreground mt-1">For initial consultation</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Emergency Cases</CardTitle>
            <AlertTriangle className="w-4 h-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-foreground">{kpis.emergency_visits}</div>
            <p className="text-xs font-medium text-red-500 mt-1">High priority alerts</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Peak Demographics</CardTitle>
            <Activity className="w-4 h-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-black text-foreground leading-tight">
              {kpis.seniors > kpis.children ? 'Seniors' : 'Children'} & {kpis.males > kpis.females ? 'Males' : 'Females'}
            </div>
            <p className="text-xs font-medium text-muted-foreground mt-1">Highest patient load</p>
          </CardContent>
        </Card>
      </div>

      {/* New Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch">
        <PatientVolumeTrend patients={patients} />
        <PatientFlowOutcome patients={patients} />
      </div>

    </div>
  );
}


