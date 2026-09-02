const axios = require("axios");

async function askLLM(prompt) {
    console.log("➡️ Appel Ollama...");
    console.log("Prompt :", prompt);

    try {
        const response = await axios.post(
            "http://127.0.0.1:11434/api/generate",
            {
                model: "qwen2.5:3b",
                prompt: prompt,
                stream: false
            },
            {
                timeout: 120000
            }
        );

        console.log("✅ Réponse Ollama reçue");
        console.log("Réponse :", response.data.response);

        return response.data.response;

    } catch (error) {
        console.error("❌ ERREUR OLLAMA");

        if (error.response) {
            console.error("Status :", error.response.status);
            console.error("Data :", error.response.data);
        } else {
            console.error("Message :", error.message);
            console.error("Code :", error.code);
        }

        throw error;
    }
}

module.exports = {
    askLLM
};