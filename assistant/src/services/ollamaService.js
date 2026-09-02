const axios = require("axios");

async function askLLM(prompt) {
    console.log("➡️ Appel Ollama...");
    console.log("Prompt :", prompt);

    try {
        const response = await axios.post(
            "http://host.docker.internal:11434/api/generate",
            {
                model: "qwen2.5:3b",
                prompt: prompt,
                stream: false
            }
        );

        console.log("📦 STATUS :", response.status);
        console.log("📦 DATA BRUTE :", JSON.stringify(response.data, null, 2));

        return response.data.response;

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