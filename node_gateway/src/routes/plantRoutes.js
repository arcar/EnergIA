const express = require("express");

const router = express.Router();
const controllersConnus = require("../controllers/plantController");



router.get("/", controllersConnus.getPlants);
router.post("/shortest_path", controllersConnus.shortest_path);
router.get("/regions", controllersConnus.getRegions);
router.get("/routes", controllersConnus.getRoutes);


module.exports = router;