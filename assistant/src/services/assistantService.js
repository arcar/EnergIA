const promptService = require("./promptService");
const ollamaService = require("./ollamaService");

async function checkKnowledge(question) {
    const mongoData =  await fetch (`${process.env.GATEWAY_URL}/api/knowledge?search=${encodeURIComponent(question)}`);
    const data = await mongoData.json();
    if (data === undefined || data.length == 0) {
        return "I don't have enough information.";
    }else {
        const package = {"question": question, "data": data};
        return package;
    }
}


async function generateAnswer(question) {
    console.log("1. Question:", question);
    const package = await checkKnowledge(question);
    console.log("2. Knowledge received:", package);
    if (typeof package === "string"){
        console.log("3. No knowledge found");
        return "there is not enough information in the database :( ."
    }else{
        const prompt = await promptService.preparePrompt(package);
        console.log("4. Prompt ready");
        const answer = await ollamaService.askOllama(prompt);
        console.log("5. Ollama answered");
        return answer
    }
}


module.exports = {generateAnswer};