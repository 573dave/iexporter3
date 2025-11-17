/**
 * iExporter3 Desktop - Annotation Modal Handler
 * Integrates HTML annotation modal with Electron backend
 */

class DesktopAnnotationModal {
    constructor() {
        this.modal = document.getElementById('annotation-modal');
        this.currentMessageId = null;
        this.currentAnnotation = null;

        // Modal elements
        this.previewText = document.getElementById('preview-text');
        this.previewAttachment = document.getElementById('preview-attachment');
        this.previewSender = document.getElementById('preview-sender');
        this.previewTimestamp = document.getElementById('preview-timestamp');
        this.noteTextarea = document.getElementById('annotation-note');
        this.charCount = document.getElementById('char-count');
        this.tagCheckboxes = document.querySelectorAll('input[name="tags"]');

        // Buttons
        this.saveButton = document.getElementById('save-annotation-btn');
        this.deleteButton = document.getElementById('delete-annotation-btn');
        this.cancelButton = document.getElementById('cancel-annotation-btn');
        this.closeButton = document.getElementById('modal-close-btn');

        this.init();
    }

    init() {
        // Set up event listeners
        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => this.saveAnnotation());
        }

        if (this.deleteButton) {
            this.deleteButton.addEventListener('click', () => this.deleteAnnotation());
        }

        if (this.cancelButton) {
            this.cancelButton.addEventListener('click', () => this.close());
        }

        if (this.closeButton) {
            this.closeButton.addEventListener('click', () => this.close());
        }

        // Close on overlay click
        const overlay = this.modal?.querySelector('.modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.close());
        }

        // Character count
        if (this.noteTextarea) {
            this.noteTextarea.addEventListener('input', () => this.updateCharCount());
        }

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal?.classList.contains('hidden')) {
                this.close();
            }
        });

        // Listen for annotate button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.annotate-btn')) {
                const button = e.target.closest('.annotate-btn');
                const messageId = button.dataset.messageId;
                this.openForMessage(messageId);
            }
        });

        console.log('Desktop Annotation Modal initialized');
    }

    /**
     * Open modal for a specific message
     */
    async openForMessage(messageId) {
        this.currentMessageId = messageId;

        // Find message element
        const messageElement = document.getElementById(messageId);
        if (!messageElement) {
            console.error('Message not found:', messageId);
            return;
        }

        // Extract message preview data
        const messageText = messageElement.querySelector('.message-text')?.textContent || '';
        const sender = messageElement.dataset.sender || 'Unknown';
        const timestamp = messageElement.dataset.timestamp;
        const attachmentImg = messageElement.querySelector('.attachment-thumbnail');

        // Populate preview
        if (this.previewText) {
            this.previewText.textContent = messageText || '(No text)';
        }

        if (this.previewSender) {
            this.previewSender.textContent = sender;
        }

        if (this.previewTimestamp && timestamp) {
            const date = new Date(parseInt(timestamp) * 1000);
            this.previewTimestamp.textContent = date.toLocaleString();
        }

        if (this.previewAttachment) {
            if (attachmentImg) {
                this.previewAttachment.innerHTML = `
                    <img src="${attachmentImg.src}" alt="Attachment preview" style="max-width: 100%; max-height: 150px; border-radius: 4px;">
                `;
            } else {
                this.previewAttachment.innerHTML = '';
            }
        }

        // Check if annotation already exists
        await this.loadExistingAnnotation(messageId);

        // Show modal
        this.show();
    }

    /**
     * Load existing annotation for message
     */
    async loadExistingAnnotation(messageId) {
        // Check if annotation exists in global annotations data
        if (window.annotationsData && window.annotationsData.annotations) {
            const existing = window.annotationsData.annotations.find(
                (a) => a.message_id === messageId
            );

            if (existing) {
                this.currentAnnotation = existing;

                // Populate form with existing data
                if (this.noteTextarea) {
                    this.noteTextarea.value = existing.note || '';
                    this.updateCharCount();
                }

                // Check tags
                this.tagCheckboxes.forEach((checkbox) => {
                    checkbox.checked = (existing.tags || []).includes(checkbox.value);
                });

                // Show delete button
                if (this.deleteButton) {
                    this.deleteButton.style.display = 'block';
                }
            } else {
                this.resetForm();
            }
        } else {
            this.resetForm();
        }
    }

    /**
     * Save annotation
     */
    async saveAnnotation() {
        // Get selected tags
        const selectedTags = Array.from(this.tagCheckboxes)
            .filter((cb) => cb.checked)
            .map((cb) => cb.value);

        if (selectedTags.length === 0) {
            alert('Please select at least one tag');
            return;
        }

        // Get note
        const note = this.noteTextarea?.value || '';

        if (!note.trim()) {
            if (!confirm('Save annotation without a note?')) {
                return;
            }
        }

        // Prepare annotation data
        const annotationData = {
            messageId: this.currentMessageId,
            tags: selectedTags,
            note: note.trim(),
            annotationId: this.currentAnnotation?.annotation_id || null,
        };

        try {
            // Disable save button
            if (this.saveButton) {
                this.saveButton.disabled = true;
                this.saveButton.textContent = 'Saving...';
            }

            // Call Electron API to save annotation
            const result = await window.electronAPI.saveAnnotation(annotationData);

            if (result.success) {
                console.log('Annotation saved:', result.annotationId);

                // Update annotations data
                this.updateAnnotationsData(result.annotationId, annotationData);

                // Close modal
                this.close();

                // Refresh annotations sidebar
                if (window.annotations) {
                    window.annotations.renderAnnotations();
                }

                // Show success message
                this.showToast('Annotation saved successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to save annotation');
            }
        } catch (error) {
            console.error('Error saving annotation:', error);
            alert('Failed to save annotation: ' + error.message);
        } finally {
            // Re-enable save button
            if (this.saveButton) {
                this.saveButton.disabled = false;
                this.saveButton.textContent = 'Save';
            }
        }
    }

    /**
     * Delete annotation
     */
    async deleteAnnotation() {
        if (!this.currentAnnotation) {
            return;
        }

        if (!confirm('Are you sure you want to delete this annotation?')) {
            return;
        }

        try {
            // Disable delete button
            if (this.deleteButton) {
                this.deleteButton.disabled = true;
                this.deleteButton.textContent = 'Deleting...';
            }

            // Call Electron API to delete annotation
            const result = await window.electronAPI.deleteAnnotation(
                this.currentAnnotation.annotation_id
            );

            if (result.success) {
                console.log('Annotation deleted');

                // Remove from annotations data
                this.removeFromAnnotationsData(this.currentAnnotation.annotation_id);

                // Close modal
                this.close();

                // Refresh annotations sidebar
                if (window.annotations) {
                    window.annotations.renderAnnotations();
                }

                // Show success message
                this.showToast('Annotation deleted', 'success');
            } else {
                throw new Error(result.error || 'Failed to delete annotation');
            }
        } catch (error) {
            console.error('Error deleting annotation:', error);
            alert('Failed to delete annotation: ' + error.message);
        } finally {
            // Re-enable delete button
            if (this.deleteButton) {
                this.deleteButton.disabled = false;
                this.deleteButton.textContent = 'Delete';
            }
        }
    }

    /**
     * Update annotations data after save
     */
    updateAnnotationsData(annotationId, data) {
        if (!window.annotationsData) {
            window.annotationsData = { annotations: [] };
        }

        // Find existing or create new
        const existing = window.annotationsData.annotations.find(
            (a) => a.annotation_id === annotationId
        );

        if (existing) {
            // Update existing
            existing.tags = data.tags;
            existing.note = data.note;
            existing.updated_at = new Date().toISOString();
        } else {
            // Add new
            window.annotationsData.annotations.push({
                annotation_id: annotationId,
                message_id: data.messageId,
                tags: data.tags,
                note: data.note,
                created_by: 'desktop-user',
                created_at: new Date().toISOString(),
            });
        }
    }

    /**
     * Remove annotation from data
     */
    removeFromAnnotationsData(annotationId) {
        if (!window.annotationsData || !window.annotationsData.annotations) {
            return;
        }

        window.annotationsData.annotations = window.annotationsData.annotations.filter(
            (a) => a.annotation_id !== annotationId
        );
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Simple toast notification (could be enhanced with a library)
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#34C759' : '#FF3B30'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Update character count
     */
    updateCharCount() {
        if (this.noteTextarea && this.charCount) {
            const length = this.noteTextarea.value.length;
            this.charCount.textContent = length.toLocaleString();

            // Warn if approaching limit
            if (length > 9000) {
                this.charCount.style.color = 'var(--color-warning)';
            } else if (length > 9500) {
                this.charCount.style.color = 'var(--color-danger)';
            } else {
                this.charCount.style.color = 'var(--color-text-tertiary)';
            }
        }
    }

    /**
     * Reset form
     */
    resetForm() {
        this.currentAnnotation = null;

        if (this.noteTextarea) {
            this.noteTextarea.value = '';
            this.updateCharCount();
        }

        this.tagCheckboxes.forEach((checkbox) => {
            checkbox.checked = false;
        });

        if (this.deleteButton) {
            this.deleteButton.style.display = 'none';
        }
    }

    /**
     * Show modal
     */
    show() {
        if (this.modal) {
            this.modal.classList.remove('hidden');
            this.noteTextarea?.focus();
        }
    }

    /**
     * Close modal
     */
    close() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            this.resetForm();
            this.currentMessageId = null;
        }
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Only initialize if in desktop mode
        if (window.electronAPI) {
            window.desktopAnnotationModal = new DesktopAnnotationModal();
            console.log('✓ Desktop annotation modal ready');
        }
    });
} else {
    if (window.electronAPI) {
        window.desktopAnnotationModal = new DesktopAnnotationModal();
        console.log('✓ Desktop annotation modal ready');
    }
}
