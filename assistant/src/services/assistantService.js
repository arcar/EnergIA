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
                        "Impossible de contacter l'API Python"
                    );
            
                }
            break;
        case "GET_PROD_NATIONALE_HEURE":
             try {
            
                    const response = await axios.post(`${process.env.PYTHON_SERVICE_URL}/repartition_heure`, result.parameters);
            
                    return response.data;
            
                } catch (error) {
            
                    console.log(error.message);
            
                    throw new Error(
                        "Impossible de contacter l'API Python222222222"
                    );
            
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