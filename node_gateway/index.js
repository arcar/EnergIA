const express = require("express");
const app = express();
app.use(express.json())
const port = 3000;
app.use(express.json());

const centraleRoutes = require("./routes/centraleRoutes");

app.use("/centrales", centraleRoutes);

app.listen(port, () => {
  console.log(`Application à l'écoute sur le port ${port}!`);
});