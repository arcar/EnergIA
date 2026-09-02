const assistantService = require("../services/assistantService");

const ollamaMessage = async (req, res) => {
    try {
        const question = req.body.prompt;

        if (!question) {
            return res.status(400).json({
                error: "Missing Question!"
            });
        }

        const answer = await assistantService.generateAnswer(question);

        return res.status(200).json({
            response: answer
        });

    } catch (error) {
        console.error("Erreur assistant :", error);

        return res.status(500).json({
            error: error.message
        });
    }
};

module.exports = {
    ollamaMessage
};