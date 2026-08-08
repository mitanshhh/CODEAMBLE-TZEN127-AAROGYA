import { Download, Users, BedDouble, AlertTriangle, Stethoscope, HeartPulse, TrendingUp, Package, Calendar, UserPlus, FileSpreadsheet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function PHCDashboard() {
  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">PHC North Overview</h2>
          <p className="text-sm text-muted-foreground mt-1">Real-time operational metrics and AI insights.</p>
        </div>
        <Button className="flex items-center gap-2">
          <Download className="w-4 h-4" />
          Generate Audit
        </Button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* KPI 1 */}
        <Card className="border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-primary mb-2">
              <Users className="w-5 h-5" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Today's Patients</span>
            </div>
            <div className="text-2xl font-semibold text-foreground">142</div>
          </CardContent>
        </Card>

        {/* KPI 2 */}
        <Card className="border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-primary mb-2">
              <BedDouble className="w-5 h-5" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Bed Occupancy</span>
            </div>
            <div className="text-2xl font-semibold text-foreground">85%</div>
          </CardContent>
        </Card>

        {/* KPI 3 */}
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-600 mb-2">
              <AlertTriangle className="w-5 h-5" />
              <span className="text-[11px] font-medium uppercase tracking-wider">Medicine Alerts</span>
            </div>
            <div className="text-2xl font-semibold text-red-600">2</div>
          </CardContent>
        </Card>

        {/* KPI 4 */}
        <Card className="border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-primary mb-2">
              <Stethoscope className="w-5 h-5" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Doctor Attendance</span>
            </div>
            <div className="text-2xl font-semibold text-foreground">5/6</div>
          </CardContent>
        </Card>

        {/* KPI 5 */}
        <Card className="border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-primary mb-2">
              <HeartPulse className="w-5 h-5" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Health Score</span>
            </div>
            <div className="text-2xl font-semibold text-foreground">
              82<span className="text-base text-muted-foreground">/100</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Bento */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Charts Area (Spans 2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Patient Footfall Chart */}
          <Card className="border-border h-80 flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-muted-foreground" />
                Patient Footfall (7 Days)
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 pb-6 pt-0">
              <div className="w-full h-full bg-muted/20 rounded border border-border flex items-center justify-center text-muted-foreground">
                [Line Chart Visualization Area]
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2 bg-secondary text-secondary-foreground hover:bg-muted/50 border-none shadow-none">
              <Package className="w-6 h-6" />
              Update Inventory
            </Button>
            <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2 bg-secondary text-secondary-foreground hover:bg-muted/50 border-none shadow-none">
              <Calendar className="w-6 h-6" />
              Duty Roster
            </Button>
            <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2 bg-secondary text-secondary-foreground hover:bg-muted/50 border-none shadow-none">
              <UserPlus className="w-6 h-6" />
              Add Patient
            </Button>
            <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2 bg-secondary text-secondary-foreground hover:bg-muted/50 border-none shadow-none">
              <FileSpreadsheet className="w-6 h-6" />
              Audit Logs
            </Button>
          </div>
        </div>

        {/* Side Panel (Spans 1 col) */}
        <div className="space-y-6">
          {/* Critical Alerts */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base font-medium text-foreground">Action Required</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 bg-red-50 p-3 rounded-lg border border-red-100">
                <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-900">Paracetamol Stock Depleted</p>
                  <p className="text-xs text-red-700 mt-1">Requested 500 units from CHC. Pending approval.</p>
                  <Button size="sm" variant="outline" className="mt-2 bg-white text-red-600 border-red-200 hover:bg-red-50">Follow Up</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Staff on Duty */}
          <Card className="border-border flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center justify-between">
                <span>Staff on Duty</span>
                <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-1 rounded-full">Shift 1 (8 AM - 4 PM)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
                    SK
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Dr. S. Kumar</p>
                    <p className="text-xs text-muted-foreground">General Physician</p>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
                    PR
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">Dr. P. Rao</p>
                    <p className="text-xs text-muted-foreground">Pediatrician</p>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
