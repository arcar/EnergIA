const express = require("express");
const cors = require('cors');
const app = express();

app.use(express.json());

app.get("/", (req, res) => {
    res.json({
        message: "Express fonctionne"
    });
});

const assistantRoute = require("./src/routes/assistantRoute.js");

app.use("/api", assistantRoute);

app.listen(3002, () => {
    console.log("Server running on port 3002");
});