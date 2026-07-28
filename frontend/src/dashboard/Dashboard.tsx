import { useEffect, useState } from "react";
import { fetchApiStatus } from "../services/api";

export function Dashboard() {
  const [status, setStatus] = useState<string>("loading");

  useEffect(() => {
    fetchApiStatus()
      .then((data) => setStatus(data.ready ? "ready" : "unknown"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <section className="dashboard">
      <h2>Dashboard</h2>
      <div className="dashboard__card">
        <p>API Status: <strong>{status}</strong></p>
        <p>SEO analysis features coming soon.</p>
      </div>
    </section>
  );
}
