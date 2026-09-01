function preparePrompt(package) {
    const question = package.question;
    const mongoData = package.data;
    const document = mongoData.map((obj, i) => {
        const tags = Array.isArray(obj.tags)? obj.tags.join(", "):obj.tags || "";
        return  `This is Document ${i + 1}, its title is: ${obj.title}, content is: ${obj.content}, category is: ${obj.category}, and its tags are: ${tags}`;
    }).join("\n");
    const rules = `
        You are BrainBox, a private knowledge assistant.
        
        STRICT RULES:
        - You must ONLY use the information inside the provided knowledge section.
        - Do NOT use your own knowledge.
        - Do NOT answer from memory.
        - Do NOT infer missing information.
        - If the answer is not explicitly contained in the provided knowledge, reply exactly:
        "I don't know based on the available knowledge."
        
        The knowledge base is the only source of truth.
        `;
    const prompt = [{role : "system", content : rules}, {role : "user", content : `knowledge: ${document}\n question: ${question}`}];
    return prompt
}

module.exports = {preparePrompt};