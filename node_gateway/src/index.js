const express = require("express");
const app = express();
app.use(express.json())
const port = 3000;
require("dotenv").config();



const plantRoutes = require("./routes/plantRoutes");
const simulationRoutes = require("./routes/simulationRoutes")
const dashboardRoutes=require("./routes/dashboardRoutes");

app.use("/plants", plantRoutes); 
app.use("/simulation", simulationRoutes)
app.use("/dashboard",dashboardRoutes)

app.listen(port, () => {
  console.log(`Application à l'écoute sur le port ${port}!`);
});