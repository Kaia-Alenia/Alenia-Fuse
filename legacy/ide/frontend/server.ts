import express from "express";
import rateLimit from "express-rate-limit";
import path from "path";
import { createServer as createViteServer } from "vite";

async function startServer() {
  const app = express();
  app.disable("x-powered-by");

  const limiter = rateLimit({
    windowMs: 60 * 1000,
    max: 100,
    message: { error: "Too many requests" }
  });
  app.use(limiter);

  const PORT = 3000;

  app.use(express.json({ limit: "1mb" }));

  // Telemetry in-memory/JSON storage file path
  const fs = await import("fs");
  const TELEMETRY_FILE = path.join(process.cwd(), "telemetry_db.json");

  interface TelemetryEvent {
    uuid: string;
    nickname: string;
    os_family: string;
    interface_type: string;
    file_type: string;
    file_count: number;
    duration_seconds: number;
    savings_bytes: number;
    timestamp: string;
  }

  // Async queue to prevent concurrent read/writes to telemetry file data loss
  let telemetryQueue = Promise.resolve();

  // Load telemetry data helper
  const loadTelemetry = async (): Promise<TelemetryEvent[]> => {
    try {
      const raw = await fs.promises.readFile(TELEMETRY_FILE, "utf8");
      return JSON.parse(raw);
    } catch (e: any) {
      if (e.code !== "ENOENT") {
        console.error("Failed to read telemetry file:", e);
      }
    }
    return [];
  };

  // Save telemetry data helper
  const saveTelemetry = async (data: TelemetryEvent[]): Promise<void> => {
    try {
      await fs.promises.writeFile(TELEMETRY_FILE, JSON.stringify(data, null, 2), "utf8");
    } catch (e) {
      console.error("Failed to write telemetry file:", e);
    }
  };

  const sanitizeLog = (val: any): string => {
    return String(val || "").replace(/[\r\n]/g, "_");
  };

  // API Route: Submit telemetry events (Upsert-like statistics)
  app.post("/api/telemetry", async (req: express.Request, res: express.Response) => {
    try {
      const { uuid, nickname, os_family, interface_type, file_type, file_count, duration_seconds, savings_bytes } = req.body;
      
      if (!uuid || !nickname) {
        res.status(400).json({ error: "uuid and nickname are required for telemetry" });
        return;
      }

      // Ensure single-threaded processing for file-based DB modifications
      telemetryQueue = telemetryQueue.then(async () => {
        const db = await loadTelemetry();
        
        // Upsert logic: if event for uuid exists, we can register/append, or update aggregate stats.
        // We will record the new event line representing a real PostgreSQL row insertion.
        const newEvent: TelemetryEvent = {
          uuid: String(uuid),
          nickname: String(nickname),
          os_family: String(os_family || "Unknown"),
          interface_type: String(interface_type || "IDE"),
          file_type: String(file_type || "unknown"),
          file_count: typeof file_count === "number" ? file_count : 1,
          duration_seconds: typeof duration_seconds === "number" ? duration_seconds : 1.5,
          savings_bytes: typeof savings_bytes === "number" ? savings_bytes : 1000,
          timestamp: new Date().toISOString()
        };

        db.push(newEvent);
        await saveTelemetry(db);

        console.log(`[Telemetry] Recorded event from ${sanitizeLog(newEvent.nickname)} (${sanitizeLog(newEvent.uuid)}): ${sanitizeLog(newEvent.file_type)} optimized.`);
        res.json({ success: true, event: newEvent });
      }).catch((error: any) => {
        console.error("Telemetry Submission Queue Error:", error);
        res.status(500).json({ error: "Failed to log telemetry" });
      });
      await telemetryQueue;

    } catch (error: any) {
      console.error("Telemetry Submission Request Error:", error);
      if (!res.headersSent) {
         res.status(500).json({ error: "Failed to process request" });
      }
    }
  });

  // API Route: Get summarized global statistics (SUM and aggregations)
  app.get("/api/telemetry/stats", async (req: express.Request, res: express.Response) => {
    try {
      const db = await loadTelemetry();
      
      // Summarize metrics
      const totalEvents = db.length;
      const totalFiles = db.reduce((sum, item) => sum + item.file_count, 0);
      const totalBytesSaved = db.reduce((sum, item) => sum + item.savings_bytes, 0);
      const uniqueUsers = new Set(db.map(item => item.uuid)).size;
      
      // OS Family breakdown
      const osBreakdown: Record<string, number> = {};
      db.forEach(item => {
        const os = item.os_family;
        osBreakdown[os] = (osBreakdown[os] || 0) + item.file_count;
      });

      // Format breakdown
      const formatBreakdown: Record<string, number> = {};
      db.forEach(item => {
        const f = item.file_type.toLowerCase();
        formatBreakdown[f] = (formatBreakdown[f] || 0) + item.file_count;
      });

      res.json({
        totalEvents,
        totalFiles,
        totalBytesSaved,
        uniqueUsers,
        osBreakdown,
        formatBreakdown,
        timestamp: new Date().toISOString()
      });
    } catch (error: any) {
      console.error("Telemetry Stats Fetch Error:", error);
      res.status(500).json({ error: "Failed to fetch stats" });
    }
  });


  // Serve static files / Vite asset pipeline
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    // SPA fallback
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "127.0.0.1", () => {
    console.log(`[Server] Running on http://127.0.0.1:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error("Server startup error:", err);
});
