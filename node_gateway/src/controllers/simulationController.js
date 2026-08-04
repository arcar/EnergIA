const pythonService = require("../services/pythonService");


async function simulation(req, res) {

    try {

        const resultat = await pythonService.simulate(req.body);

        res.json(resultat);

    } catch(error) {

        res.status(500).json({
            message: error.message
        });

    }

}


module.exports = {
    simulation
};