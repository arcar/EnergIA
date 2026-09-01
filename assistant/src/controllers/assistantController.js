const assistantService = require("../services/assistantService");

const ollamaMessage = async (req, res) => {
    try {
        const question = req.query.search;
        if(!question){
            return res.status(400).json({
                error: "Missing Question!"
            });
        }
        const reply = await assistantService.generateAnswer(question);
        res.status(200).json(reply);
        return 
    }catch (error){
            console.error(error);

    return res.status(500).json({
        error: error.message,
        stack: error.stack
    });
        }
}

module.exports = {ollamaMessage};