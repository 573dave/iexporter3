/**
 * Main Viewer Initialization
 * Coordinates all viewer modules
 */

class Viewer {
    constructor() {
        this.mode = this.detectMode();
        this.init();
    }

    detectMode() {
        // Detect viewer mode from body class
        const body = document.body;
        if (body.classList.contains('annotated-mode')) {
            return 'annotated';
        } else if (body.classList.contains('clean-mode')) {
            return 'clean';
        }
        return 'clean';
    }

    init() {
        console.log('iExporter3 Viewer initialized in', this.mode, 'mode');

        // Log forensic metadata
        this.logMetadata();

        // Performance monitoring
        this.monitorPerformance();
    }

    logMetadata() {
        const metadata = {
            caseId: document.querySelector('meta[name="case-id"]')?.content,
            conversationId: document.querySelector('meta[name="conversation-id"]')?.content,
            partNumber: document.querySelector('meta[name="part-number"]')?.content,
            totalParts: document.querySelector('meta[name="total-parts"]')?.content,
            exportTimestamp: document.querySelector('meta[name="export-timestamp"]')?.content,
            exportHash: document.querySelector('meta[name="export-hash"]')?.content,
        };

        console.log('Forensic Metadata:', metadata);
    }

    monitorPerformance() {
        // Log page load performance
        window.addEventListener('load', () => {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;

            console.log('Page Load Performance:', {
                totalTime: pageLoadTime + 'ms',
                domContentLoaded: (perfData.domContentLoadedEventEnd - perfData.navigationStart) + 'ms',
                domInteractive: (perfData.domInteractive - perfData.navigationStart) + 'ms',
            });

            // Check if we met performance targets (<2s for 10k messages)
            if (pageLoadTime > 2000) {
                console.warn('Page load time exceeds target (2000ms):', pageLoadTime + 'ms');
            } else {
                console.log('✓ Page load time meets target (<2000ms)');
            }
        });
    }
}

// Initialize viewer on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.viewer = new Viewer();
    });
} else {
    window.viewer = new Viewer();
}
