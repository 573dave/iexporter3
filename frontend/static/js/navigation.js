/**
 * Navigation Module
 * Jump to messages, part selection, smooth scrolling
 */

class Navigation {
    constructor() {
        this.jumpButton = document.getElementById('jump-btn');
        this.messageIdInput = document.getElementById('message-id-input');
        this.partSelect = document.getElementById('part-select');

        this.init();
    }

    init() {
        // Jump to message button
        if (this.jumpButton && this.messageIdInput) {
            this.jumpButton.addEventListener('click', () => {
                this.jumpToMessage(this.messageIdInput.value.trim());
            });

            this.messageIdInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.jumpToMessage(this.messageIdInput.value.trim());
                }
            });
        }

        // Part selection (if multi-part conversation)
        if (this.partSelect) {
            this.partSelect.addEventListener('change', (e) => {
                this.switchPart(parseInt(e.target.value));
            });
        }

        // Handle annotation click navigation
        document.addEventListener('annotation-clicked', (e) => {
            this.jumpToMessage(e.detail.messageId);
        });
    }

    jumpToMessage(messageId) {
        if (!messageId) {
            console.warn('No message ID provided');
            return;
        }

        // Find message element
        const messageElement = document.getElementById(messageId);

        if (!messageElement) {
            console.warn('Message not found:', messageId);
            alert(`Message ${messageId} not found in current part`);
            return;
        }

        // Scroll to message
        this.scrollToElement(messageElement);

        // Highlight message temporarily
        this.highlightMessage(messageElement);

        // Clear input
        if (this.messageIdInput) {
            this.messageIdInput.value = '';
        }
    }

    scrollToElement(element) {
        // Smooth scroll to element
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
        });
    }

    highlightMessage(element) {
        // Add highlight class
        element.classList.add('highlighted');

        // Remove highlight after animation
        setTimeout(() => {
            element.classList.remove('highlighted');
        }, 1500);
    }

    switchPart(partNumber) {
        // Navigate to different conversation part
        const currentUrl = window.location.href;
        const urlParts = currentUrl.split('/');
        const filename = urlParts[urlParts.length - 1];

        // Replace part number in filename
        // Assumes format: conversation_001.html
        const newFilename = filename.replace(/conversation_\d{3}/, `conversation_${String(partNumber).padStart(3, '0')}`);

        // Navigate to new part
        window.location.href = newFilename;
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.navigation = new Navigation();
    });
} else {
    window.navigation = new Navigation();
}
