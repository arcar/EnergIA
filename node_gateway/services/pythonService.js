const axios = require("axios");


async function getCentrales(){

    const response = await axios.get(
        "http://localhost:5000/centrales"
    );

    return response.data;

}


module.exports = {
    getCentrales
};