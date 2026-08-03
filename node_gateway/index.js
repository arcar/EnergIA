const express = require("express");
const app = express();
app.use(express.json())
const port = 3000;
app.use(express.json());

const plantRoutes = require("./routes/plantRoutes");

app.use("/plants", plantRoutes);

app.listen(port, () => {
  console.log(`Application à l'écoute sur le port ${port}!`);
});