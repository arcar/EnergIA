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

async function shortest_path(req, res) {

    try {

        const { start, goal, weight } = req.body;


        const cheminCourt = await pythonService.shortest_path(
            start,
            goal,
            weight
        );


        res.json(cheminCourt);


    } catch (error) {

        res.status(503).json({
            message: error.message
        });

    }

}



module.exports = {
    getPlants, shortest_path
};