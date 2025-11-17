/**
 * Hash Verification Module
 * Verifies evidence integrity on page load
 */

class HashVerification {
    constructor() {
        this.statusElement = document.getElementById('hash-status');
        this.verifyButton = document.getElementById('verify-hash-btn');
        this.expectedHash = null;

        this.init();
    }

    init() {
        // Run verification on load
        this.verify();

        // Re-verify button
        if (this.verifyButton) {
            this.verifyButton.addEventListener('click', () => {
                this.verify();
            });
        }
    }

    async verify() {
        this.setStatus('loading', 'Verifying...');

        try {
            // Load hash metadata from .hash.json
            const hashData = await this.loadHashMetadata();

            if (!hashData) {
                this.setStatus('missing', 'Cannot verify - hash file missing');
                return;
            }

            this.expectedHash = hashData.export_hash;

            // Calculate current hash of evidence layer
            const currentHash = await this.calculateCurrentHash();

            // Compare hashes
            if (currentHash === this.expectedHash) {
                this.setStatus('verified', 'Evidence Verified ✓');
            } else {
                this.setStatus('failed', 'Evidence Modified - Hash Mismatch');
                console.error('Hash mismatch:', {
                    expected: this.expectedHash,
                    actual: currentHash
                });
            }

        } catch (error) {
            console.error('Hash verification error:', error);
            this.setStatus('missing', 'Verification failed');
        }
    }

    async loadHashMetadata() {
        try {
            // Determine hash file path based on current HTML file
            const partNumber = document.querySelector('meta[name="part-number"]')?.content || '1';
            const hashFilePath = `./conversation_${partNumber.padStart(3, '0')}.hash.json`;

            const response = await fetch(hashFilePath);
            if (!response.ok) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.warn('Could not load hash metadata:', error);
            return null;
        }
    }

    async calculateCurrentHash() {
        // In a real implementation, this would:
        // 1. Extract evidence layer content (messages without annotations)
        // 2. Normalize line endings
        // 3. Calculate SHA-256 hash
        // 4. Return hex string

        // For now, return a placeholder
        // TODO: Implement actual hash calculation using Web Crypto API

        // Get evidence content (messages container)
        const evidenceContent = this.extractEvidenceContent();

        // Calculate SHA-256
        const hash = await this.sha256(evidenceContent);

        return hash;
    }

    extractEvidenceContent() {
        // Extract only the evidence layer (messages without annotation UI)
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) {
            return '';
        }

        // Clone the container to avoid modifying DOM
        const clone = messagesContainer.cloneNode(true);

        // Remove annotation buttons and indicators (not part of evidence)
        clone.querySelectorAll('.annotate-btn, .annotation-indicator').forEach(el => el.remove());

        // Get normalized HTML
        return clone.innerHTML.trim();
    }

    async sha256(content) {
        // Use Web Crypto API to calculate SHA-256
        const encoder = new TextEncoder();
        const data = encoder.encode(content);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }

    setStatus(state, message) {
        if (!this.statusElement) return;

        // Remove all state classes
        this.statusElement.classList.remove('loading', 'verified', 'failed', 'missing');

        // Add current state
        this.statusElement.classList.add(state);

        // Update message (remove spinner if present)
        const spinner = this.statusElement.querySelector('.spinner');
        if (spinner) {
            spinner.remove();
        }

        // Update text
        const span = this.statusElement.querySelector('span') || document.createElement('span');
        span.textContent = message;

        if (!this.statusElement.querySelector('span')) {
            this.statusElement.appendChild(span);
        }
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.hashVerification = new HashVerification();
    });
} else {
    window.hashVerification = new HashVerification();
}
