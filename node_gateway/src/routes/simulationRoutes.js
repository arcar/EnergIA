const express = require("express");
const router = express.Router();

const simulationController = require("../controllers/simulationController");


router.post("/", simulationController.repartition_heure);

router.get("/regions", simulationController.repartition);


module.exports = router;