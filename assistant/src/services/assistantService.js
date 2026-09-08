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
                const response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/repartition_heure`, result.parameters);      
                const data = response.data;
                const heure = data.heure;
                const resultats = data.resultats;

                let message = `Répartition nationale à ${heure} :\n\n`;

                resultats.forEach((plant) => {
                    message += `- ${plant.plant_name} : ${plant.production_mw.toFixed(0)} MW\n`;
                });

                return message
                               
                } catch (error) {
            
                    console.log(error.message);
            
                    throw new Error(
                        "Impossible de contacter l'API Python 2"
                    );
            
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

        case "GET_PERTURBATION":
            try {
                const response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/perturber_consommation`, result.parameters)
                return "La production à été perturber comme moi <:)"
            }catch (error) {
                console.log(error.message);
            
                    throw new Error(
                        "Impossible de contacter l'API Python 4"
                    );
            }
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