async function askReply(request) {
    const reply = await fetch(
        `${process.env.ASSISTANT_URL}/api/chat`,
        {
            method: "POST",
            body: JSON.stringify({
                prompt: request
            })
        }
    );

    const data = await reply.json();
    console.log("FROM ASSISTANT SERVICE:", data);

    return data;
}

module.exports = {askReply}