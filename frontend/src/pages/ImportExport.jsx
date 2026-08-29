import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function ImportExport() {
  const { token, isManager } = useAuth();
  const [itemsReport, setItemsReport] = useState(null);
  const [receiptsReport, setReceiptsReport] = useState(null);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  async function handleItemsImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    setError(""); setItemsReport(null);
    try {
      const report = await api.importItems(token, file);
      setItemsReport(report);
    } catch (err) {
      setError(err.message);
    } finally {
      e.target.value = "";
    }
  }

  async function handleReceiptsImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    setError(""); setReceiptsReport(null);
    try {
      const report = await api.importReceipts(token, file);
      setReceiptsReport(report);
    } catch (err) {
      setError(err.message);
    } finally {
      e.target.value = "";
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      const blob = await api.exportStock(token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "stock_position.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Import / export</h1>
          <p className="subtitle">Bulk-load items or receipts from CSV, or export the current stock position.</p>
        </div>
      </div>

      {error && <div className="alert-banner">{error}</div>}

      <div className="card">
        <div className="section-title">Export current stock position</div>
        <p style={{ marginTop: 0 }}>One row per item per location, including locations with zero on hand.</p>
        <button className="btn btn-primary" onClick={handleExport} disabled={exporting}>
          {exporting ? "Preparing…" : "Download stock_position.csv"}
        </button>
      </div>

      {isManager && (
        <>
          <div className="card">
            <div className="section-title">Bulk import items</div>
            <p style={{ marginTop: 0 }}>
              CSV columns: <code className="mono">sku, name, description, unit_of_measure, reorder_level, category</code>.
              The category must already exist. Valid rows are imported even if others in the file fail.
            </p>
            <input type="file" accept=".csv" onChange={handleItemsImport} />
            {itemsReport && <ImportReportView report={itemsReport} />}
          </div>

          <div className="card">
            <div className="section-title">Bulk import receipts</div>
            <p style={{ marginTop: 0 }}>
              CSV columns: <code className="mono">sku, location, quantity</code>. Each valid row becomes one receipt movement.
            </p>
            <input type="file" accept=".csv" onChange={handleReceiptsImport} />
            {receiptsReport && <ImportReportView report={receiptsReport} />}
          </div>
        </>
      )}
    </div>
  );
}

function ImportReportView({ report }) {
  return (
    <div style={{ marginTop: 14 }}>
      <p>
        <strong>{report.imported}</strong> of {report.total_rows} rows imported
        {report.failed > 0 && <span style={{ color: "var(--danger)" }}> · {report.failed} failed</span>}.
      </p>
      {report.failed > 0 && (
        <table>
          <thead><tr><th>Row</th><th>Status</th><th>Message</th></tr></thead>
          <tbody>
            {report.results.filter((r) => r.status === "error").map((r) => (
              <tr key={r.row}><td>{r.row}</td><td style={{ color: "var(--danger)" }}>{r.status}</td><td>{r.message}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
