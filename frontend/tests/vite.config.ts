import { defineConfig } from "vite";

const totals = new Map([
  ["below-half-cent", 1.004],
  ["half-cent", 1.005],
]);

export default defineConfig({
  cacheDir: ".vite/revenue-tests",
  define: {
    "import.meta.env.VITE_API_URL": "window.location.origin",
    "import.meta.env.VITE_BACKEND_URL": "window.location.origin",
  },
  plugins: [
    {
      name: "revenue-response-fixtures",
      configureServer(server) {
        server.middlewares.use((request, response, next) => {
          const url = new URL(request.url ?? "/", "http://test");
          if (url.pathname === "/api/v1/auth/me") {
            response.setHeader("Content-Type", "application/json");
            response.end("{}");
            return;
          }
          const propertyId = url.searchParams.get("property_id");
          const total = totals.get(propertyId ?? "");
          if (
            url.pathname === "/api/v1/dashboard/summary" &&
            total !== undefined
          ) {
            response.setHeader("Content-Type", "application/json");
            response.end(
              JSON.stringify({
                property_id: propertyId,
                total_revenue: total,
                currency: "USD",
                reservations_count: 1,
              }),
            );
            return;
          }
          next();
        });
      },
    },
  ],
  server: {
    host: "127.0.0.1",
    port: 5179,
    strictPort: true,
  },
});
