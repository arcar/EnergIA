const pythonService = require("../services/pythonService");


async function getPlants(req, res) {

    try {

        const centrales = await pythonService.getPlants();

        res.json(centrales);

    } catch (error) {

        res.status(503).json({
            message: error.message
        });

    }

}


module.exports = {
    getPlants
};