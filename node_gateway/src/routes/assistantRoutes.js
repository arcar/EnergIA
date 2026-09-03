const express = require("express");
const assistant = require('../controllers/assistantController');

const router = express.Router();

router.get("/assistant", (req,res,next)=>{
    console.log("assistant route hit");
    next();
}, assistant.chat);

module.exports = router;