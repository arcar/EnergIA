const express = require("express");
const app = express();
app.use(express.json())
const port = 3000;
require("dotenv").config();



const plantRoutes = require("./routes/plantRoutes");
const simulationRoutes = require("./routes/simulationRoutes")

app.use("/plants", plantRoutes); 
app.use("/simulation", simulationRoutes)
// app.use("/api/regions", plantRoutes);

app.listen(port, () => {
  console.log(`Application à l'écoute sur le port ${port}!`);
});