import { format, startOfWeek, endOfWeek, subWeeks, subDays, startOfMonth, subMonths, endOfMonth, isAfter } from 'date-fns';
import { enIN } from 'date-fns/locale';

// Constants for Period Selector
export type PeriodOption = 
  | 'Today'
  | 'This Week'
  | 'Previous Week'
  | 'Last 7 Days'
  | 'This Month'
  | 'Previous Month'
  | 'This Year'
  | 'Custom Range';

export interface DateRange {
  start: Date;
  end: Date;
  label: string;
}

/**
 * We use Monday as the start of the week for all calculations.
 * weekStartsOn: 1 (Monday)
 */
const WEEK_OPTIONS = { weekStartsOn: 1 as const };

/**
 * Formats a date exactly as: 23 Aug 2026, 10:42 AM
 */
export function formatExactTimestamp(date: Date | string | null): string {
  if (!date) return '--';
  const d = new Date(date);
  return format(d, "dd MMM yyyy, hh:mm a", { locale: enIN });
}

/**
 * Gets date range for various standardized periods.
 */
export function getPeriodRange(period: PeriodOption, customStart?: Date, customEnd?: Date): DateRange {
  const now = new Date();
  
  switch (period) {
    case 'Today':
      return { start: now, end: now, label: 'Today' };
    
    case 'This Week':
      return { 
        start: startOfWeek(now, WEEK_OPTIONS), 
        end: endOfWeek(now, WEEK_OPTIONS),
        label: `${format(startOfWeek(now, WEEK_OPTIONS), 'MMM dd')} - ${format(endOfWeek(now, WEEK_OPTIONS), 'MMM dd, yyyy')}`
      };
      
    case 'Previous Week': {
      const prevWeek = subWeeks(now, 1);
      return {
        start: startOfWeek(prevWeek, WEEK_OPTIONS),
        end: endOfWeek(prevWeek, WEEK_OPTIONS),
        label: `${format(startOfWeek(prevWeek, WEEK_OPTIONS), 'MMM dd')} - ${format(endOfWeek(prevWeek, WEEK_OPTIONS), 'MMM dd, yyyy')}`
      };
    }
      
    case 'Last 7 Days':
      return {
        start: subDays(now, 6),
        end: now,
        label: `${format(subDays(now, 6), 'MMM dd')} - ${format(now, 'MMM dd, yyyy')}`
      };
      
    case 'This Month':
      return {
        start: startOfMonth(now),
        end: endOfMonth(now),
        label: format(now, 'MMMM yyyy')
      };
      
    case 'Previous Month': {
      const prevMonth = subMonths(now, 1);
      return {
        start: startOfMonth(prevMonth),
        end: endOfMonth(prevMonth),
        label: format(prevMonth, 'MMMM yyyy')
      };
    }
      
    case 'This Year':
      return {
        start: new Date(now.getFullYear(), 0, 1),
        end: new Date(now.getFullYear(), 11, 31),
        label: format(now, 'yyyy')
      };
      
    case 'Custom Range':
      return {
        start: customStart || now,
        end: customEnd || now,
        label: `${format(customStart || now, 'MMM dd')} - ${format(customEnd || now, 'MMM dd, yyyy')}`
      };
      
    default:
      return getPeriodRange('This Week');
  }
}

/**
 * Checks if a given date is in the future.
 */
export function isFutureDate(date: Date | string): boolean {
  return isAfter(new Date(date), new Date());
}
