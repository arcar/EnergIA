const ollamaService = require("./ollamaService");

let buffer = "";

process.stdin.on("data", (chunk) => {
    buffer += chunk;
    const lines = buffer.split("\n");
    buffer = lines.pop();

    for (const line of lines){
        if(!line.trim()) continue;
        handeLine(line);
    }
})

async function handeLine(line){
    let request;
    try {
        request = JSON.parse(line)
    } catch (e) {
        console.error("Erreur de parsing JSON:", e);
        return;
    }

    
}


async function generateAnswer(question) {
    console.log("Question reçue :", question);

    const answer = await ollamaService.askLLM(question);

    console.log("Réponse Ollama reçue");

    return answer;
}

module.exports = {
    generateAnswer
};