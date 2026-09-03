const axios = require("axios");
const { Ollama } = require("ollama");
const SYSTEM_PROMPT = require("./protocol");

const ollamaClient = new Ollama({
    host: process.env.OLLAMA_URL
});

async function askLLM(prompt) {
    console.log("➡️ Appel Ollama...");
    console.log("Prompt :", prompt);
    console.log("SYSTEM PROMPT :", SYSTEM_PROMPT);

    try {
        const response = await ollamaClient.chat({
            model: "qwen2.5:3b",
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

        return response.message.content;

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