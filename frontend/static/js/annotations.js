/**
 * Annotations Manager
 * Display, filter, and navigate annotations
 */

class AnnotationsManager {
    constructor(annotationsData) {
        this.data = annotationsData || { annotations: [] };
        this.annotations = this.data.annotations || [];
        this.filteredAnnotations = [...this.annotations];

        this.listElement = document.getElementById('annotations-list');
        this.tagCheckboxes = document.querySelectorAll('.tag-checkboxes input[type="checkbox"]');

        this.init();
    }

    init() {
        // Update tag counts
        this.updateTagCounts();

        // Render annotations
        this.renderAnnotations();

        // Set up tag filter listeners
        this.tagCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filterAnnotations();
            });
        });

        // Set up lightbox for images
        this.setupImageLightbox();
    }

    updateTagCounts() {
        const counts = {
            'Key': 0,
            'Timeline': 0,
            'Privileged': 0,
            'WorkProduct': 0
        };

        this.annotations.forEach(annotation => {
            (annotation.tags || []).forEach(tag => {
                if (counts.hasOwnProperty(tag)) {
                    counts[tag]++;
                }
            });
        });

        // Update UI
        Object.keys(counts).forEach(tag => {
            const countElement = document.getElementById(`count-${tag.toLowerCase()}`);
            if (countElement) {
                countElement.textContent = `(${counts[tag]})`;
            }
        });
    }

    filterAnnotations() {
        // Get selected tags
        const selectedTags = Array.from(this.tagCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        // Filter annotations
        if (selectedTags.length === 0) {
            this.filteredAnnotations = [];
        } else {
            this.filteredAnnotations = this.annotations.filter(annotation => {
                return (annotation.tags || []).some(tag => selectedTags.includes(tag));
            });
        }

        // Re-render
        this.renderAnnotations();
    }

    renderAnnotations() {
        if (!this.listElement) return;

        // Clear existing content
        this.listElement.innerHTML = '';

        if (this.filteredAnnotations.length === 0) {
            // Show empty state
            this.listElement.innerHTML = `
                <div class="empty-state">
                    <p>No annotations match the selected filters.</p>
                </div>
            `;
            return;
        }

        // Render each annotation
        this.filteredAnnotations.forEach(annotation => {
            const annotationElement = this.createAnnotationElement(annotation);
            this.listElement.appendChild(annotationElement);
        });
    }

    createAnnotationElement(annotation) {
        const div = document.createElement('div');
        div.className = 'annotation-item';

        // Add primary tag class for border color
        if (annotation.tags && annotation.tags.length > 0) {
            div.classList.add(`tag-${annotation.tags[0].toLowerCase()}`);
        }

        // Tags HTML
        const tagsHTML = (annotation.tags || [])
            .map(tag => `<span class="tag-badge tag-${tag.toLowerCase()}">${tag}</span>`)
            .join('');

        // Format timestamp
        const timestamp = annotation.created_at_iso ?
            new Date(annotation.created_at_iso).toLocaleString() :
            'Unknown';

        div.innerHTML = `
            <div class="annotation-header-info">
                <div class="annotation-tags">${tagsHTML}</div>
            </div>
            <div class="annotation-message-id">${annotation.message_id}</div>
            ${annotation.note ? `<div class="annotation-note-preview">${this.escapeHtml(annotation.note)}</div>` : ''}
            <div class="annotation-meta">
                <span>${annotation.created_by}</span>
                <span>•</span>
                <span>${timestamp}</span>
            </div>
        `;

        // Click to jump to message
        div.addEventListener('click', () => {
            // Dispatch custom event for navigation
            document.dispatchEvent(new CustomEvent('annotation-clicked', {
                detail: { messageId: annotation.message_id }
            }));
        });

        return div;
    }

    setupImageLightbox() {
        // Set up image lightbox for attachments
        const lightbox = document.getElementById('image-lightbox');
        const lightboxImage = document.getElementById('lightbox-image');
        const lightboxFilename = document.getElementById('lightbox-filename');
        const lightboxClose = document.querySelector('.lightbox-close');
        const lightboxOverlay = document.querySelector('.lightbox-overlay');

        if (!lightbox) return;

        // Click handler for attachment thumbnails
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('attachment-thumbnail')) {
                const originalPath = e.target.dataset.original;
                const filename = e.target.alt;

                lightboxImage.src = originalPath;
                lightboxFilename.textContent = filename;
                lightbox.classList.remove('hidden');
            }
        });

        // Close lightbox
        const closeLightbox = () => {
            lightbox.classList.add('hidden');
            lightboxImage.src = '';
        };

        if (lightboxClose) {
            lightboxClose.addEventListener('click', closeLightbox);
        }

        if (lightboxOverlay) {
            lightboxOverlay.addEventListener('click', closeLightbox);
        }

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !lightbox.classList.contains('hidden')) {
                closeLightbox();
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in HTML template
window.AnnotationsManager = AnnotationsManager;
