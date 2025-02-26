document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const fileInput = document.getElementById("file-input");
    const chatMessages = document.getElementById("chat-messages");
    const imagePreview = document.getElementById("image-preview");
    const newChatButton = document.getElementById("new-chat-button");

    // Auto-resize textarea
    messageInput.addEventListener("input", () => {
        messageInput.style.height = "auto";
        messageInput.style.height = `${messageInput.scrollHeight}px`;
    });

    // Send with Enter key
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Preview uploaded image
    fileInput.addEventListener("change", () => {
        imagePreview.innerHTML = "";
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            imagePreview.appendChild(img);
        }
    });

    // Handle form submission
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        const file = fileInput.files[0];
        if (!message && !file) return;

        // Display user message
        const userMessage = document.createElement("div");
        userMessage.classList.add("message", "user-message");
        if (message) userMessage.textContent = message;
        if (file) {
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            userMessage.appendChild(img);
        }
        chatMessages.appendChild(userMessage);

        // Clear inputs
        messageInput.value = "";
        fileInput.value = "";
        imagePreview.innerHTML = "";
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Show loading indicator
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("loading");
        loadingDiv.innerHTML = '<div class="spinner"></div>';
        chatMessages.appendChild(loadingDiv);

        try {
            const formData = new FormData();
            if (message) formData.append("query", message);
            if (file) formData.append("image", file);

            const response = await fetch("/chat", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Network error");
            const data = await response.json();

            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);

            // Display bot response with Markdown and images
            const botMessage = document.createElement("div");
            botMessage.classList.add("message", "bot-message");
            botMessage.innerHTML = marked.parse(data.response || "");
            if (data.images && data.images.length > 0) {
                const imageContainer = document.createElement("div");
                imageContainer.classList.add("image-message");
                data.images.forEach((url) => {
                    const img = document.createElement("img");
                    img.src = url;
                    img.onclick = () => window.open(`/gallery/${url.split('/').pop()}`, '_blank');
                    imageContainer.appendChild(img);
                });
                botMessage.appendChild(imageContainer);
            }
            chatMessages.appendChild(botMessage);

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            chatMessages.removeChild(loadingDiv);
            const errorMessage = document.createElement("div");
            errorMessage.classList.add("message", "bot-message");
            errorMessage.textContent = "Sorry, something went wrong.";
            chatMessages.appendChild(errorMessage);
        }
    });

    // New Chat button
    newChatButton.addEventListener("click", () => {
        chatMessages.innerHTML = `
            <div class="message bot-message">
                Hello! I'm your AI assistant. How can I help you today?
            </div>
        `;
    });
});