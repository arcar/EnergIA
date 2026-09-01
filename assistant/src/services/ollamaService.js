const { Ollama } = require('ollama');

const ollamaClient = new Ollama({
    host: process.env.OLLAMA_URL
});
async function askOllama(prompt) {
    const response = await ollamaClient.chat({
        model: 'qwen2.5:3b',
        messages : prompt
    })
    return response.message.content;
}

module.exports = {askOllama};