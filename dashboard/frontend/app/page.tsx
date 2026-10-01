"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

type Detection = {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  center: [number, number];
};

type Decision = {
  frame_id: number;
  action: "SORT" | "WAIT" | "REVIEW" | "NO_DETECTION";
  reason: string;
  target_bin: string | null;
  stable_count: number;
  required_stable_frames: number;
  mean_stable_confidence: number;
  current_class?: string;
  current_confidence?: number;
};

type InferenceResponse = {
  model_id: string;
  detections: Detection[];
  best_detection: Detection | null;
  latency_ms: number;
  image_width: number;
  image_height: number;
  fps_estimate_from_inference: number | null;
  decision: Decision;
};

type ModelMetric = {
  id: string;
  label: string;
  status: string;
  family: string;
  precision: number | null;
  recall: number | null;
  map50: number | null;
  map5095: number | null;
  notes: string;
};

type MetricsResponse = {
  models: ModelMetric[];
  classwise_map50: {
    classes: string[];
    [key: string]: string[] | number[];
  };
  dataset: {
    images: Record<string, number>;
    objects: Record<string, number>;
  };
};

type HealthResponse = {
  ok: boolean;
  model_ready: boolean;
  model: {
    id: string;
    label: string;
    loaded: boolean;
    model_path: string;
    model_exists: boolean;
    load_error: string | null;
  };
};

type LogSummary = {
  records: number;
  actions: Record<string, number>;
  classes: Record<string, number>;
  avg_latency_ms: number | null;
};

type ReviewItem = {
  timestamp: string;
  frame_id: string;
  queue_type: string;
  filename: string;
  class_name: string;
  confidence: number;
  reason: string;
};

const classLabels = ["electronic", "glass", "metal", "others", "paper", "plastic"];

function pct(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function metric(value: number | null | undefined) {
  return value == null ? "—" : value.toFixed(3);
}

export default function Dashboard() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const captureRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const inferBusyRef = useRef(false);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metricsData, setMetricsData] = useState<MetricsResponse | null>(null);
  const [logSummary, setLogSummary] = useState<LogSummary | null>(null);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [inference, setInference] = useState<InferenceResponse | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [robotVideoError, setRobotVideoError] = useState(false);

  const refreshStaticData = useCallback(async () => {
    try {
      const [healthRes, metricsRes, logsRes, reviewRes] = await Promise.all([
        fetch(`${API_BASE}/api/health`, { cache: "no-store" }),
        fetch(`${API_BASE}/api/metrics`, { cache: "no-store" }),
        fetch(`${API_BASE}/api/logs/summary`, { cache: "no-store" }),
        fetch(`${API_BASE}/api/review?limit=12`, { cache: "no-store" }),
      ]);
      if (!healthRes.ok) throw new Error("Backend health check failed");
      setHealth(await healthRes.json());
      setMetricsData(await metricsRes.json());
      setLogSummary(await logsRes.json());
      const reviewJson = await reviewRes.json();
      setReviewItems(reviewJson.items || []);
      setApiError(null);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Could not reach backend");
    }
  }, []);

  useEffect(() => {
    refreshStaticData();
    const interval = window.setInterval(refreshStaticData, 5000);
    return () => window.clearInterval(interval);
  }, [refreshStaticData]);

  const drawOverlay = useCallback((result: InferenceResponse | null) => {
    const canvas = overlayRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!result) return;

    const scaleX = canvas.width / result.image_width;
    const scaleY = canvas.height / result.image_height;
    ctx.lineWidth = 3;
    ctx.font = "18px Inter, system-ui, sans-serif";

    for (const detection of result.detections) {
      const [x1, y1, x2, y2] = detection.bbox;
      const x = x1 * scaleX;
      const y = y1 * scaleY;
      const w = (x2 - x1) * scaleX;
      const h = (y2 - y1) * scaleY;

      ctx.strokeStyle = detection === result.best_detection ? "#65e4a3" : "#8aa0b5";
      ctx.fillStyle = "rgba(5, 14, 22, 0.82)";
      ctx.strokeRect(x, y, w, h);

      const text = `${detection.class_name.toUpperCase()} ${(detection.confidence * 100).toFixed(1)}%`;
      const textWidth = ctx.measureText(text).width + 18;
      ctx.fillRect(x, Math.max(0, y - 30), textWidth, 28);
      ctx.fillStyle = "#f8fbff";
      ctx.fillText(text, x + 9, Math.max(20, y - 10));
    }
  }, []);

  const inferFrame = useCallback(async () => {
    if (!videoRef.current || !captureRef.current || !cameraOn || inferBusyRef.current) return;
    const video = videoRef.current;
    if (video.readyState < 2) return;

    inferBusyRef.current = true;
    try {
      const capture = captureRef.current;
      capture.width = 640;
      capture.height = 480;
      const ctx = capture.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, 640, 480);

      const blob = await new Promise<Blob | null>((resolve) => capture.toBlob(resolve, "image/jpeg", 0.82));
      if (!blob) return;

      const form = new FormData();
      form.append("frame", blob, "camera.jpg");
      const response = await fetch(`${API_BASE}/api/infer`, { method: "POST", body: form });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Inference failed (${response.status})`);
      }

      const result: InferenceResponse = await response.json();
      setInference(result);
      setApiError(null);
      drawOverlay(result);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Inference failed");
    } finally {
      inferBusyRef.current = false;
    }
  }, [cameraOn, drawOverlay]);

  useEffect(() => {
    if (!cameraOn) return;
    timerRef.current = window.setInterval(inferFrame, 450);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [cameraOn, inferFrame]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
      await fetch(`${API_BASE}/api/reset`, { method: "POST" }).catch(() => null);
      setApiError(null);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Camera permission failed");
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOn(false);
    setInference(null);
    drawOverlay(null);
  };

  useEffect(() => () => streamRef.current?.getTracks().forEach((track) => track.stop()), []);

  const activeModel = metricsData?.models.find((item) => item.id === health?.model.id);
  const best = inference?.best_detection;
  const decision = inference?.decision;
  const datasetObjects = metricsData?.dataset.objects || {};
  const maxObjects = Math.max(...classLabels.map((name) => datasetObjects[name] || 0), 1);

  const actionClass = useMemo(() => {
    const action = decision?.action || "NO_DETECTION";
    return `decision-badge decision-${action.toLowerCase().replace("_", "-")}`;
  }, [decision?.action]);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">WasteNet-RoboSort</p>
          <h1>Research & Robotic Waste Sorting Dashboard</h1>
          <p className="subtitle">Live perception, decision gating, benchmark evidence, and a recorded robot demonstration in one interface.</p>
        </div>
        <div className="system-status">
          <span className={`status-dot ${health?.model_ready ? "online" : "offline"}`} />
          <div>
            <strong>{health?.model_ready ? "Model ready" : "Model not loaded"}</strong>
            <span>{health?.model.label || "Checking backend..."}</span>
          </div>
        </div>
      </header>

      {apiError && <div className="alert"><strong>System notice:</strong> {apiError}</div>}

      <section className="kpi-grid">
        <MetricCard label="Active model" value={activeModel?.label || health?.model.label || "—"} note={activeModel?.status || "runtime"} />
        <MetricCard label="mAP50" value={metric(activeModel?.map50)} note="held-out local test" />
        <MetricCard label="mAP50-95" value={metric(activeModel?.map5095)} note="held-out local test" />
        <MetricCard label="Live latency" value={inference ? `${inference.latency_ms.toFixed(1)} ms` : "—"} note="model inference only" />
        <MetricCard label="Runtime records" value={(logSummary?.records ?? 0).toLocaleString()} note="dashboard session archive" />
      </section>

      <section className="workspace-grid">
        <article className="panel live-panel">
          <PanelHeader title="Live Detection" kicker="Camera + current model" action={cameraOn ? "LIVE" : "OFF"} />
          <div className="camera-shell">
            <video ref={videoRef} className="camera-video" playsInline muted />
            <canvas ref={overlayRef} width={640} height={480} className="camera-overlay" />
            {!cameraOn && (
              <div className="camera-placeholder">
                <span className="camera-icon">◎</span>
                <strong>Camera is off</strong>
                <p>Start the camera to classify and detect waste with the current model.</p>
              </div>
            )}
          </div>
          <canvas ref={captureRef} className="hidden-canvas" />
          <div className="camera-controls">
            {!cameraOn ? (
              <button className="primary-button" onClick={startCamera}>Start camera</button>
            ) : (
              <button className="secondary-button" onClick={stopCamera}>Stop camera</button>
            )}
            <span>Inference interval: ~450 ms</span>
          </div>
        </article>

        <article className="panel decision-panel">
          <PanelHeader title="Decision Gate" kicker="Research control logic" action={decision?.action || "IDLE"} />
          <div className="decision-main">
            <span className={actionClass}>{decision?.action || "NO DETECTION"}</span>
            <h2>{best ? best.class_name.toUpperCase() : "Waiting for an object"}</h2>
            <p>{decision?.reason?.replaceAll("_", " ") || "The model has not produced a live decision yet."}</p>
          </div>
          <div className="decision-stats">
            <InfoRow label="Confidence" value={best ? pct(best.confidence) : "—"} />
            <InfoRow label="Stable frames" value={decision ? `${decision.stable_count}/${decision.required_stable_frames}` : "—"} />
            <InfoRow label="Mean stable confidence" value={decision ? pct(decision.mean_stable_confidence) : "—"} />
            <InfoRow label="Target bin" value={decision?.target_bin?.toUpperCase() || "—"} />
            <InfoRow label="Detections in frame" value={String(inference?.detections.length ?? 0)} />
          </div>
          <div className="gate-progress">
            <div className="gate-progress-fill" style={{ width: `${Math.min(100, ((decision?.stable_count || 0) / (decision?.required_stable_frames || 3)) * 100)}%` }} />
          </div>
          <p className="microcopy">Current gate mirrors the existing research logic: temporal class stability + confidence threshold. Spatial consistency can be added in the next research revision without changing the UI contract.</p>
        </article>
      </section>

      <section className="workspace-grid lower-grid">
        <article className="panel robot-panel">
          <PanelHeader title="Robotic Arm Demonstration" kicker="Pre-recorded presentation media" action="VIDEO" />
          <div className="robot-video-shell">
            {!robotVideoError ? (
              <video controls preload="metadata" onError={() => setRobotVideoError(true)}>
                <source src="/robot-arm-demo.mp4" type="video/mp4" />
              </video>
            ) : (
              <div className="video-placeholder">
                <strong>Robot demo video not added yet</strong>
                <p>Copy your final MP4 to <code>dashboard/frontend/public/robot-arm-demo.mp4</code>.</p>
              </div>
            )}
          </div>
          <p className="microcopy">This panel intentionally uses a recorded physical-robot demonstration. The live presentation does not depend on the robotic hand being connected.</p>
        </article>

        <article className="panel dataset-panel">
          <PanelHeader title="Dataset Snapshot" kicker="Local held-out research dataset" action="596 IMAGES" />
          <div className="dataset-bars">
            {classLabels.map((label) => {
              const count = datasetObjects[label] || 0;
              return (
                <div className="bar-row" key={label}>
                  <span className="bar-label">{label}</span>
                  <div className="bar-track"><div className="bar-fill" style={{ width: `${(count / maxObjects) * 100}%` }} /></div>
                  <strong>{count}</strong>
                </div>
              );
            })}
          </div>
          <div className="split-row">
            <span>Train <strong>{metricsData?.dataset.images.train ?? 415}</strong></span>
            <span>Validation <strong>{metricsData?.dataset.images.validation ?? 85}</strong></span>
            <span>Test <strong>{metricsData?.dataset.images.test ?? 96}</strong></span>
          </div>
        </article>
      </section>

      <section className="panel model-lab">
        <PanelHeader title="Model Lab" kicker="Evaluated models now, new models later" action="CONTROLLED COMPARISON" />
        <div className="table-wrap">
          <table>
            <thead><tr><th>Model</th><th>Status</th><th>Precision</th><th>Recall</th><th>mAP50</th><th>mAP50-95</th><th>Role</th></tr></thead>
            <tbody>
              {(metricsData?.models || []).map((model) => (
                <tr key={model.id} className={health?.model.id === model.id ? "active-row" : ""}>
                  <td><strong>{model.label}</strong><span className="table-sub">{model.family}</span></td>
                  <td><span className={`status-chip ${model.status}`}>{model.status}</span></td>
                  <td>{metric(model.precision)}</td>
                  <td>{metric(model.recall)}</td>
                  <td>{metric(model.map50)}</td>
                  <td>{metric(model.map5095)}</td>
                  <td>{model.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="workspace-grid lower-grid">
        <article className="panel">
          <PanelHeader title="Runtime Activity" kicker="Dashboard-generated evidence" action={`${logSummary?.records ?? 0} RECORDS`} />
          <div className="activity-grid">
            {["SORT", "WAIT", "REVIEW", "NO_DETECTION"].map((name) => (
              <div className="activity-card" key={name}><span>{name.replace("_", " ")}</span><strong>{logSummary?.actions?.[name] || 0}</strong></div>
            ))}
          </div>
          <InfoRow label="Average inference latency" value={logSummary?.avg_latency_ms == null ? "—" : `${logSummary.avg_latency_ms.toFixed(1)} ms`} />
          <InfoRow label="Review queue items shown" value={String(reviewItems.length)} />
        </article>

        <article className="panel">
          <PanelHeader title="Review Queue" kicker="Uncertain + unknown samples" action="HUMAN-IN-THE-LOOP" />
          <div className="review-list">
            {reviewItems.length === 0 ? (
              <div className="empty-state">No dashboard review samples yet. Low-confidence or unknown camera frames will appear here.</div>
            ) : reviewItems.slice(0, 6).map((item) => (
              <div className="review-item" key={`${item.timestamp}-${item.filename}`}>
                <div><strong>{item.class_name || "unknown"}</strong><span>{item.queue_type} · {pct(item.confidence)}</span></div>
                <small>{item.reason.replaceAll("_", " ")}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <footer>
        <span>WasteNet-RoboSort research dashboard · current-model stabilization phase</span>
        <span>Backend: {API_BASE}</span>
      </footer>
    </main>
  );
}

function PanelHeader({ title, kicker, action }: { title: string; kicker: string; action: string }) {
  return <div className="panel-header"><div><span>{kicker}</span><h3>{title}</h3></div><strong>{action}</strong></div>;
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="metric-card"><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return <div className="info-row"><span>{label}</span><strong>{value}</strong></div>;
}
