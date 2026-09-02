async function askReply(request) {
    const reply = await fetch(
        `${process.env.ASSISTANT_URL}/api/chat?search=${encodeURIComponent(request)}`,
        {
            method: "POST"
        }
    );

    const data = await reply.json();
    console.log("FROM ASSISTANT SERVICE:", data);

    return data;
}

module.exports = {askReply}