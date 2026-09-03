const express = require("express");
require("dotenv").config();
const cors = require('cors');

const app = express();

app.use(cors());

app.use(express.json());

const plantRoutes = require("./src/routes/plantRoutes");
const simulationRoutes = require("./src/routes/simulationRoutes")
const assistantRoutes = require("./src/routes/assistantRoutes")

app.use("/assistant", assistantRoutes)
app.use("/plants", plantRoutes); 
app.use("/repartition_heure", simulationRoutes)

app.listen(3000, () => {
  console.log(`Application à l'écoute sur le port 3000!`);
});