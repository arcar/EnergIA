const axios = require("axios");


async function getPlants() {

    try {

        const response = await axios.get(
            "http://127.0.0.1:8000/plants"
        );

        return response.data;

    } catch (error) {

        throw new Error(
            "Impossible de contacter l'API Python"
        );

    }

}


module.exports = {
    getPlants
};