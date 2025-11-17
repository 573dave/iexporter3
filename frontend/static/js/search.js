/**
 * Search Module
 * Full-text search within current conversation part
 */

class Search {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchButton = document.getElementById('search-btn');
        this.resultsContainer = document.getElementById('search-results');
        this.resultsList = document.getElementById('search-results-list');
        this.messagesContainer = document.getElementById('messages-container');

        this.messages = [];
        this.results = [];

        this.init();
    }

    init() {
        // Index messages for search
        this.indexMessages();

        // Search button click
        if (this.searchButton) {
            this.searchButton.addEventListener('click', () => {
                this.performSearch();
            });
        }

        // Search on Enter key
        if (this.searchInput) {
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    indexMessages() {
        // Extract all messages from DOM for searching
        if (!this.messagesContainer) return;

        const messageElements = this.messagesContainer.querySelectorAll('.message-wrapper');

        messageElements.forEach(element => {
            const messageId = element.id;
            const textElement = element.querySelector('.message-text');
            const text = textElement ? textElement.textContent : '';
            const timestamp = element.dataset.timestamp;
            const sender = element.dataset.sender;

            this.messages.push({
                id: messageId,
                text: text,
                timestamp: timestamp,
                sender: sender,
                element: element
            });
        });

        console.log(`Indexed ${this.messages.length} messages for search`);
    }

    performSearch() {
        const query = this.searchInput.value.trim().toLowerCase();

        if (!query) {
            this.hideResults();
            return;
        }

        // Search messages
        this.results = this.messages.filter(message => {
            return message.text.toLowerCase().includes(query);
        });

        // Display results
        this.displayResults();
    }

    displayResults() {
        if (!this.resultsContainer || !this.resultsList) return;

        // Show results container
        this.resultsContainer.classList.remove('hidden');

        // Update count
        const countElement = this.resultsContainer.querySelector('.results-count');
        if (countElement) {
            countElement.textContent = `${this.results.length} result${this.results.length !== 1 ? 's' : ''}`;
        }

        // Clear previous results
        this.resultsList.innerHTML = '';

        if (this.results.length === 0) {
            this.resultsList.innerHTML = '<li style="text-align: center; color: var(--color-text-tertiary);">No matches found</li>';
            return;
        }

        // Render results
        this.results.forEach(result => {
            const li = document.createElement('li');

            // Highlight query in preview
            const preview = this.getPreviewWithHighlight(result.text, this.searchInput.value);

            li.innerHTML = `
                <div><strong>${result.id}</strong></div>
                <div class="result-preview">${preview}</div>
            `;

            li.addEventListener('click', () => {
                this.jumpToResult(result);
            });

            this.resultsList.appendChild(li);
        });
    }

    getPreviewWithHighlight(text, query) {
        const queryLower = query.toLowerCase();
        const textLower = text.toLowerCase();
        const index = textLower.indexOf(queryLower);

        if (index === -1) {
            return text.substring(0, 100) + (text.length > 100 ? '...' : '');
        }

        // Get context around match
        const start = Math.max(0, index - 30);
        const end = Math.min(text.length, index + query.length + 70);

        let preview = text.substring(start, end);

        // Add ellipsis
        if (start > 0) preview = '...' + preview;
        if (end < text.length) preview = preview + '...';

        // Highlight match (simple replacement)
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        preview = preview.replace(regex, '<mark>$1</mark>');

        return preview;
    }

    jumpToResult(result) {
        // Dispatch navigation event
        document.dispatchEvent(new CustomEvent('annotation-clicked', {
            detail: { messageId: result.id }
        }));

        // Hide results
        this.hideResults();

        // Clear search input
        this.searchInput.value = '';
    }

    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.classList.add('hidden');
        }
    }

    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.search = new Search();
    });
} else {
    window.search = new Search();
}
