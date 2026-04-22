const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const path = require("path");
require("dotenv").config();

// Initialize database tables
require("./User"); // Create users table
require("./db"); // Create AOI table (already included in db.js)

const authRoutes = require("./routes/auth");
const aoiRoutes = require("./routes/aoi");
const weatherRoutes = require("./routes/weather");
const indicesRoutes = require("./routes/indices");

const app = express();
const PORT = process.env.PORT || 3001;

// ✅ Enhanced CORS Middleware - Production Ready
const corsOptions = {
  origin: process.env.NODE_ENV === "production" ? true : "*",
  credentials: true,
  optionsSuccessStatus: 200,
  allowedHeaders: ["Content-Type", "Authorization"],
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
};

app.use(cors(corsOptions));

// ✅ Middleware
app.use(bodyParser.json());

// ✅ Serve static frontend files
const frontendPath = path.join(__dirname, "../frontend/build");
app.use(express.static(frontendPath));

// ✅ Routes
app.use("/auth", authRoutes); // Authentication routes
app.use("/api/fields", aoiRoutes); // AOI-related routes (Get/Post AOI data)
app.use("/api/weather", weatherRoutes); // Weather-related routes
app.use("/api/indices", indicesRoutes); // Vegetation indices routes (proxies to Flask)

// ✅ Serve frontend for all other routes (SPA fallback)
app.get("*", (req, res) => {
  res.sendFile(path.join(frontendPath, "index.html"));
});

// ✅ Start server
app.listen(PORT, "0.0.0.0", () => {
  const host = process.env.HOSTNAME || "localhost";
  const protocol = process.env.NODE_ENV === "production" ? "https" : "http";
  console.log(`🚀 Server running on ${protocol}://${host}:${PORT}`);
  console.log(`📱 Accessible from: http://0.0.0.0:${PORT}`);
});
