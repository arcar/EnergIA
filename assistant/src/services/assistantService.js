const ollamaService = require("./ollamaService");
const axios = require("axios");


async function generateAnswer(question) {
    console.log("Question reçue :", question);

    const result = await ollamaService.askLLM(question);

    switch (result.action){
        case "GET_PLANTS":
            try {

                    const response = await axios.get(`${process.env.PYTHON_SERVICE_URL}/plants`);

                    return response.data;

                } catch (error) {

                    console.log(error.message);

                    throw new Error(
                        "Impossible de contacter l'API Python 1"
                    );

                }
            break;

        case "GET_PROD_NATIONALE_HEURE":
            try {
                const { date } = result.parameters;
                const dateComparaison = new Date(date);
                const dateLimite = new Date("2026-06-30");

                let response;

                if (dateComparaison <= dateLimite) {
                    // Ancienne API (jusqu'au 30/06/2026 inclus)
                    response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/repartition_heure`, result.parameters);

                } else {
                    // Nouvelle API (à partir du 01/07/2026) — à compléter manuellement
                    response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/predict/repartition_heure`, result.parameters);
                }

                const { heure, resultats } = response.data;

                let message = `Répartition nationale le ${date} à ${heure} :\n\n`;

                resultats.forEach((plant) => {
                    message += `- ${plant.plant_name} : ${plant.production_mw.toFixed(0)} MW - saturation ${plant.taux_utilisation_percent.toFixed(2)}%\n`;
                });

                return message;

            } catch (error) {
                console.log(error.message);
                throw new Error("Impossible de contacter l'API Python 2");
            }
            break;

        case "GET_CONSO_REGION_HEURE":
            try {

                const response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/conso_regionale_horaire`, result.parameters);

                return `À ${response.data.heure}, la consommation de la région ${response.data.region} est de ${response.data.consommation} MW.`;

            } catch (error) {

                console.log(error.message);
                console.log("STATUS:", error.response?.status);
                console.log("DATA:", error.response?.data);
                console.log("PARAMS ENVOYÉS:", result.parameters);

                throw new Error(
                    "Impossible de contacter l'API Python 3"
                );

            }
            break;
        case "GET_PREDICTION_CONSO":
            try {
                const response = await axios.post(
                    `${process.env.PYTHON_SERVICE_URL}/predict/conso_regionale`,
                    result.parameters
                );

                return `Le ${response.data.date.split("-").reverse().join("/")} à ${response.data.heure}, la consommation prévue de la région ${response.data.id_region.charAt(0).toUpperCase() + response.data.id_region.slice(1).replaceAll("_", " ")} est de ${response.data.consommation_predite.toFixed(2)} MW.`;
            } catch (error) {
                console.log(error.message);
                console.log("STATUS:", error.response?.status);
                console.log("DATA:", error.response?.data);
                console.log("PARAMS ENVOYÉS:", result.parameters);
                throw new Error(
                    "Impossible de récupérer la prédiction de consommation"
                );
            }
            break;

      case "GET_PERTURBATION":
        try {
            const response=await axios.post(`${process.env.PYTHON_SERVICE_URL}/predict/perturber_consommation`,result.parameters);
            console.log(response)

            return {
                    parameters:result.parameters,
                    states:response.data.resultats
            };
        } catch(error) {
                console.log(error.message);
                console.log("STATUS:",error.response?.status);
                console.log("DATA:",error.response?.data);
                console.log("PARAMS ENVOYÉS:",result.parameters);
                throw new Error(
                    "Impossible de contacter l'API Python 4"
                );
            }
            break;
        case "RESET_SCENARIO":
            try {
                const response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/reinitialiser_scenario`);
                return "Tous les scénarios ont été réinitialisés, retour aux données d'origine.";
            } catch (error) {
                console.log(error.message);
                throw new Error("Impossible de contacter l'API Python 5");
            }
            break;
        case "UNKNOWN":
            try {

                    const response = "Je n'ai pas les informations à ma disposition pour vous répondre";

                    return response;

                } catch (error) {

                    console.log(error.message);

                    throw new Error(
                        "Impossible de contacter l'API Python!!!!!!!!!!!!!!!!!!"
                    );

                }

            }


    console.log("Réponse Ollama reçue");
}

module.exports = {
    generateAnswer
};