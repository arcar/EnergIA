const pythonService = require("../services/pythonService.js");


async function getPlants(req,res){

    console.log("Récupération des centrales");

    try{

        const plants = await pythonService.getPlants();

        console.log("Centrales récupérées");

        res.json({
            success:true,
            data:plants
        });


    }catch(error){

        console.error("Erreur récupération centrales :", error.message);

        res.status(500).json({
            success:false,
            message:"Impossible de récupérer les centrales",
            status:500
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
    getPlants, getRoutes, getRegions
};