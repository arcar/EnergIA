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


module.exports = {
    getPlants
};