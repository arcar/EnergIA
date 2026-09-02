async function askReply(request) {
    console.log("➡️ Calling assistant:", process.env.ASSISTANT_URL);
    const reply = await fetch(
    `${process.env.ASSISTANT_URL}/api/chat`,
    {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            prompt: request
        })
    }
    );

     console.log("Assistant HTTP status:", reply.status);

    const data = await reply.json();

    console.log("FROM ASSISTANT SERVICE:", data);

    return data;
}

module.exports = {askReply}