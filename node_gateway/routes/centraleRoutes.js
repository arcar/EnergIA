const express = require("express");

const router = express.Router();
const { getCentrales } = require("../controllers/centraleController");


router.get("/", getCentrales);


module.exports = router;