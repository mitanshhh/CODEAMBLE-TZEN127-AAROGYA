"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PeriodOption, getPeriodRange, DateRange } from "@/lib/dateUtils";

interface PeriodSelectorProps {
  value: PeriodOption;
  onChange: (value: PeriodOption, range: DateRange) => void;
  options?: PeriodOption[];
}

export function PeriodSelector({ 
  value, 
  onChange,
  options = ['Today', 'This Week', 'Previous Week', 'This Month', 'Previous Month', 'This Year']
}: PeriodSelectorProps) {

  const handleValueChange = (val: string) => {
    const period = val as PeriodOption;
    const range = getPeriodRange(period);
    onChange(period, range);
  };

  const currentRange = React.useMemo(() => getPeriodRange(value), [value]);

  return (
    <div className="flex flex-col gap-1">
      <Select value={value} onValueChange={(val) => handleValueChange(val || '')}>
        <SelectTrigger className="w-[200px] bg-white border-slate-200 text-slate-700 shadow-sm font-medium hover:bg-slate-50 transition-colors focus:ring-blue-500 rounded-lg">
          <SelectValue placeholder="Select Period" />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt} value={opt}>
              {opt}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <span className="text-xs text-muted-foreground font-medium px-1">
        {currentRange.label}
      </span>
    </div>
  );
}
