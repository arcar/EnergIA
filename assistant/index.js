const express = require("express");
require("dotenv").config();

const app = express();

app.use(express.json());

const assistantRoute = require('./src/routes/assistantRoute');

app.use("/api", assistantRoute);

app.listen(3002, () => {
  console.log(`Server running on port 3002`);
});