const express = require("express");

const router = express.Router();
const controllersConnus = require("../controllers/plantController");



router.get("/", controllersConnus.getPlants);
router.get("/regions", controllersConnus.getRegions);
router.get("/routes", controllersConnus.getRoutes);


module.exports = router;