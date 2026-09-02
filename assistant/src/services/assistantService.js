const ollamaService = require("./ollamaService");

async function generateAnswer(question) {
    console.log("Question reçue :", question);

    const answer = await ollamaService.askLLM(question);

    console.log("Réponse Ollama reçue");

    return answer;
}

module.exports = {
    generateAnswer
};