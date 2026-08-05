const pythonService = require("../services/pythonService.js");


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
async function getRegions (req, res) {
    try {

        const regions = await pythonService.getRegions();

        res.status(200).json(regions);

    } catch (error) {

        console.error(error);

        res.status(500).json({
            message: "Impossible de récupérer les régions."
        });

    }
};


async function getRoutes(req, res) {

    try {

        const { regionId } = req.query;

        const routes = await pythonService.getRoutes(regionId);

        res.status(200).json(routes);

    } catch (error) {

        if (error.response) {
            return res
                .status(error.response.status)
                .json(error.response.data);
        }

        console.error(error);

        res.status(500).json({
            message: "Erreur lors du calcul des routes."
        });

    }

};


module.exports = {
    getPlants, shortest_path, getRoutes, getRegions
};