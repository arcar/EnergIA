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
        case "GET_CONSO":

            break;
    }

    console.log("Réponse Ollama reçue");
}

module.exports = {
    generateAnswer
};