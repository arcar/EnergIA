const pythonService = require("../services/pythonService");


async function simulation(req, res) {

    console.log("Simulation demandée");
    console.log("Région :", req.body.region);
    console.log("Augmentation :", req.body.augmentation, "MW");

    try {

        const resultat = await pythonService.simulate(req.body);

        console.log("Simulation terminée");

        res.json({
            success: true,
            data: resultat
        });

    } catch(error){

        console.log("Erreur simulation :", error);

        res.status(error.status || 500).json({
            success:false,
            message:"Impossible d'effectuer la simulation",
            error:error.message || error,
            status:error.status || 500
        });

    }
}

async function repartition_heure(req, res) {

    console.log("repartition demandée");
    console.log("Heure :", req.body.heure);
  
    try {

        const resultat = await pythonService.repartir_heure(req.body);

        console.log("Repartition terminée");

        res.json({
            success: true,
            data: resultat
        });

    } catch(error){

        console.log("Erreur répartition :", error);

        res.status(error.status || 500).json({
            success:false,
            message:"Impossible d'effectuer la répartition",
            error:error.message || error,
            status:error.status || 500
        });

    }
}

module.exports = {
    simulation, repartition_heure
};