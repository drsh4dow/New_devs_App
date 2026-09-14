import React, { useEffect, useState } from "react";
import { SecureAPI } from "../lib/secureApi";
import type { RevenueData, RevenuePeriod } from "../lib/secureApi";

interface RevenueSummaryProps {
  propertyId: string;
  period?: RevenuePeriod;
  showRaw?: boolean;
}

export const RevenueSummary: React.FC<RevenueSummaryProps> = ({
  propertyId,
  period,
  showRaw,
}) => {
  const [data, setData] = useState<RevenueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const month = period?.month;
  const year = period?.year;

  useEffect(() => {
    let active = true;
    const fetchRevenue = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await SecureAPI.getDashboardSummary(
          propertyId,
          month !== undefined && year !== undefined
            ? { month, year }
            : undefined,
        );
        if (active) setData(response);
      } catch (err) {
        if (active) {
          setError("Failed to load revenue data");
          console.error(err);
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    void fetchRevenue();
    return () => {
      active = false;
    };
  }, [propertyId, month, year]);

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-100 rounded w-1/4"></div>
          <div className="h-8 bg-gray-100 rounded w-1/2"></div>
          <div className="flex gap-4 pt-4">
            <div className="h-12 bg-gray-100 rounded flex-1"></div>
            <div className="h-12 bg-gray-100 rounded flex-1"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error)
    return (
      <div role="alert" className="p-4 text-red-500 bg-red-50 rounded-lg">
        {error}
      </div>
    );
  if (!data) return null;

  // Format directly: multiplying a binary float by 100 can round a half-cent down.
  const displayTotal = data.total_revenue.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {showRaw && (
        <div className="p-3 bg-gray-50 text-xs font-mono border-b border-gray-100 overflow-auto max-h-32">
          <strong className="block mb-1 text-gray-500 uppercase tracking-wider text-[10px]">
            Raw API Response
          </strong>
          <pre className="text-gray-700">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}

      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            Total Revenue
          </h2>
          <p className="text-3xl font-bold text-gray-900 tracking-tight mt-1">
            {data.currency} {displayTotal}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              Property ID
            </p>
            <p className="text-sm font-semibold text-gray-700 font-mono mt-1">
              {data.property_id}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              Reservations
            </p>
            <p className="text-sm font-semibold text-gray-700 mt-1">
              {data.reservations_count}{" "}
              <span className="font-normal text-gray-400">bookings</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
