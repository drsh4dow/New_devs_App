import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../contexts/AuthContext.new";
import { SecureAPI } from "../lib/secureApi";
import { RevenueSummary } from "./RevenueSummary";

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [selectedProperty, setSelectedProperty] = useState("");
  const [reportingMonth, setReportingMonth] = useState("");
  const {
    data: properties,
    isPending,
    isError,
  } = useQuery({
    queryKey: ["dashboard-properties", user?.id],
    queryFn: () => SecureAPI.getDashboardProperties(),
    enabled: Boolean(user),
  });

  if (!user) return null;
  if (isPending) return <p className="p-6">Loading properties…</p>;
  if (isError)
    return (
      <p role="alert" className="p-6">
        Failed to load properties.
      </p>
    );
  if (properties.length === 0)
    return <p className="p-6">No properties found.</p>;

  const property =
    properties.find((item) => item.id === selectedProperty) ?? properties[0];
  const [year, month] = reportingMonth.split("-").map(Number);
  const period = reportingMonth ? { month, year } : undefined;

  return (
    <div className="p-4 lg:p-6 min-h-full">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">
          Property Management Dashboard
        </h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 lg:p-6">
          <div className="mb-6 flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
            <div>
              <h2 className="text-lg lg:text-xl font-medium text-gray-900 mb-2">
                Revenue Overview
              </h2>
              <p className="text-sm lg:text-base text-gray-600">
                {reportingMonth
                  ? "Revenue by property-local check-in month"
                  : "All-time revenue"}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <div>
                <label
                  htmlFor="revenue-property"
                  className="block text-xs font-medium text-gray-700 mb-1"
                >
                  Select Property
                </label>
                <select
                  id="revenue-property"
                  value={property.id}
                  onChange={(event) => setSelectedProperty(event.target.value)}
                  className="block w-full min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  {properties.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="revenue-month"
                  className="block text-xs font-medium text-gray-700 mb-1"
                >
                  Reporting month
                </label>
                <input
                  id="revenue-month"
                  type="month"
                  min="0001-01"
                  max="9998-12"
                  value={reportingMonth}
                  onChange={(event) => {
                    if (event.target.validity.valid)
                      setReportingMonth(event.target.value);
                  }}
                  aria-describedby="revenue-month-help"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <p
                  id="revenue-month-help"
                  className="text-xs text-gray-500 mt-1"
                >
                  Leave empty for all time.
                </p>
              </div>
            </div>
          </div>

          <RevenueSummary
            key={`${user.id}:${property.id}:${reportingMonth}`}
            propertyId={property.id}
            period={period}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
