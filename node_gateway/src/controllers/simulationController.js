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

    } catch(error) {

        console.error("Erreur simulation :", error.message);

        res.status(500).json({
            success: false,
            message: "Impossible d'effectuer la simulation",
            error: error.message,
            status: 500
        });

    }

}


module.exports = {
    simulation
};