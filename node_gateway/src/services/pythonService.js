const axios = require("axios");


async function getPlants() {

    console.log("URL Python :", process.env.PYTHON_SERVICE_URL);

    try {

        const response = await axios.get(
            `${process.env.PYTHON_SERVICE_URL}/plants`
        );

        return response.data;

    } catch (error) {

        console.log(error.message);

        throw new Error(
            "Impossible de contacter l'API Python"
        );

    }

}

async function simulate(data) {

    try {

        const response = await axios.post(
            `${process.env.PYTHON_SERVICE_URL}/simulation`,
            data
        );

        return response.data;

    } catch (error) {

        // Python a répondu avec une erreur
        if (error.response) {

            throw {
                status: error.response.status,
                message: error.response.data
            };

        }

        // Python inaccessible
        throw {
            status: 503,
            message: "Impossible de contacter l'API Python"
        };
    }
}

async function repartir_heure(data) {

    try {

        const response = await axios.post(
            `${process.env.PYTHON_SERVICE_URL}/repartition_heure`,
            data
        );

        return response.data;

    } catch (error) {

        // Python a répondu avec une erreur
        if (error.response) {

            throw {
                status: error.response.status,
                message: error.response.data
            };

        }

        // Python inaccessible
        throw {
            status: 503,
            message: "Impossible de contacter l'API Python"
        };
    }
}


async function getRegions() {
    const { data } = await axios.get(`${process.env.PYTHON_SERVICE_URL}/regions`);
    return data;
}

async function getRoutes(regionId) {
    const { data } = await axios.get(
        `${process.env.PYTHON_SERVICE_URL}/regions/routes/${regionId}`
    );

    return data;
}

module.exports = {
    getPlants, simulate, getRegions, getRoutes, repartir_heure
};