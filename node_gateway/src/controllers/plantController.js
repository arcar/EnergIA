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