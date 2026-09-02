const assistantService = require('../services/assistantService');

const chat = async (req, res) => {
    try {
        const question = req.query.request;

        console.log("Gateway received:", question);

        const assistantReply = await assistantService.askReply(question);
        
        console.log("Reply from assistant:", assistantReply);

        res.json(assistantReply);

    } catch(error) {
        console.error(error);
        res.status(500).json({
            error: error.message
        });
    }
}

module.exports = {chat};