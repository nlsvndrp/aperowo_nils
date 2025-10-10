const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

const rootDir = __dirname;
const publicDir = path.join(rootDir, "public");
const dataDir = path.resolve(rootDir, "../data");

const resolveDataPath = (relativePath = "") => {
  const normalised = relativePath.startsWith("/")
    ? relativePath.slice(1)
    : relativePath;
  const candidate = path.resolve(dataDir, normalised);

  if (!candidate.startsWith(dataDir)) {
    return null;
  }

  return candidate;
};

app.use(express.static(publicDir, { extensions: ["html"] }));

app.get("/data/*", (req, res, next) => {
  const target = resolveDataPath(req.params[0]);

  if (!target) {
    res.status(404).send("Not found");
    return;
  }

  fs.stat(target, (err, stats) => {
    if (err || !stats.isFile()) {
      next();
      return;
    }

    res.type("application/json");
    res.sendFile(target);
  });
});

app.use((req, res) => {
  res.status(404).send("Not found");
});

app.listen(PORT, () => {
  console.log(`Aperowo frontend running at http://localhost:${PORT}`);
});
