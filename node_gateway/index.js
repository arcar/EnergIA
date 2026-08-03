const express = require("express");
const app = express();
app.use(express.json())
const port = 3000;

app.get("/health", (req, res) => {

  return res.status(200).json({"message":"Hello World!"});
});

app.listen(port, () => {
  console.log(`Application à l'écoute sur le port ${port}!`);
});