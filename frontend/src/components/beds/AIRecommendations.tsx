"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Sparkles, AlertCircle } from "lucide-react";

export function AIRecommendations({ alerts }: { alerts: string[] }) {
  if (!alerts || alerts.length === 0) {
    return (
      <Alert className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 mb-6">
        <Sparkles className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-800 font-bold tracking-wide text-xs uppercase">AI Insights</AlertTitle>
        <AlertDescription className="text-blue-700 font-medium">
          Bed occupancy is stable. No critical anomalies detected.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-3 mb-6">
      {alerts.map((alert, idx) => (
        <Alert key={idx} variant={alert.includes('CRITICAL') ? 'destructive' : 'default'} className={alert.includes('CRITICAL') ? '' : 'bg-orange-50 text-orange-800 border-orange-200'}>
          <AlertCircle className={`h-4 w-4 ${alert.includes('CRITICAL') ? '' : 'text-orange-600'}`} />
          <AlertTitle className="font-bold tracking-wide text-xs uppercase">{alert.includes('CRITICAL') ? 'Critical Alert' : 'AI Recommendation'}</AlertTitle>
          <AlertDescription className="font-medium mt-1">
            {alert.replace('CRITICAL: ', '')}
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
}
