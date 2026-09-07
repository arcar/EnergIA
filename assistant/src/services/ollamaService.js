const axios = require("axios");
const { Ollama } = require("ollama");
const SYSTEM_PROMPT = require("./protocol");

const ollamaClient = new Ollama({
    host: process.env.OLLAMA_URL
});


function normalizeHour(hour) {
    let [h, m] = hour.split(":").map(Number);

    if (m <= 7) m = 0;
    else if (m <= 22) m = 15;
    else if (m <= 37) m = 30;
    else if (m <= 52) m = 45;
    else {
        m = 0;
        h++;
    }

    if (h === 24) h = 0;

    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}



async function askLLM(prompt) {
    console.log("➡️ Appel Ollama...");
    console.log("Prompt :", prompt);
    // console.log("SYSTEM PROMPT :", SYSTEM_PROMPT);

    try {
        const response = await ollamaClient.chat({
            model: "qwen2.5:7b",
            messages: [
                {role : "system", content : SYSTEM_PROMPT},
                {
                    role: "user",
                    content: prompt
                }
            ],
            stream: false
        });

        console.log("✅ Réponse Ollama reçue");
        console.log("Réponse complète :", response);
        console.log("Texte :", response.message.content);

        const result = JSON.parse(response.message.content);

        if (result.action === "GET_PROD_NATIONALE_HEURE" && result.parameters.heure) {
            result.parameters.heure = normalizeHour(result.parameters.heure);
        }
        if (result.action === "GET_CONSO_REGION_HEURE" && result.parameters.heure) {
            result.parameters.heure = normalizeHour(result.parameters.heure);
        }
        return result;


    } catch (error) {
        console.error("❌ ERREUR OLLAMA");
        console.error("Message :", error.message);
        console.error("Code :", error.code);
        throw error;
    }
}

module.exports = {
    askLLM
};