const express = require("express");

const router = express.Router();
const { getPlants} = require("../controllers/plantController");


router.get("/", getPlants);


module.exports = router;