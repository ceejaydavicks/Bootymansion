// Main JavaScript for BootyMansion
class BootyMansion {
    constructor() {
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.lightboxOpen = false;
        this.currentMediaIndex = 0;
        this.mediaItems = [];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initLazyLoading();
        this.initInfiniteScroll();
        this.preloadImages();
    }
    
    bindEvents() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        if (searchInput && searchBtn) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            searchBtn.addEventListener('click', () => this.handleSearch(searchInput.value));
            
            // Search on Enter key
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch(e.target.value);
                }
            });
        }
        
        // Category filter events
        this.bindCategoryEvents();
        
        // Lightbox events
        this.bindLightboxEvents();
        
        // Smooth scroll for category bar
        this.initCategoryScroll();
        
        // Admin form events
        this.bindAdminFormEvents();
    }
    
    bindCategoryEvents() {
        const categoryBtns = document.querySelectorAll('.category-btn');
        categoryBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Don't prevent default for links with href
                const category = btn.dataset.category;
                if (category) {
                    this.filterByCategory(category);
                    this.updateActiveCategoryBtn(btn);
                }
            });
        });
    }
    
    bindLightboxEvents() {
        const lightboxOverlay = document.getElementById('lightboxOverlay');
        const lightboxClose = document.getElementById('lightboxClose');
        const lightboxPrev = document.getElementById('lightboxPrev');
        const lightboxNext = document.getElementById('lightboxNext');
        
        if (lightboxClose) lightboxClose.addEventListener('click', () => this.closeLightbox());
        if (lightboxPrev) lightboxPrev.addEventListener('click', () => this.navigateLightbox(-1));
        if (lightboxNext) lightboxNext.addEventListener('click', () => this.navigateLightbox(1));
        
        if (lightboxOverlay) {
            lightboxOverlay.addEventListener('click', (e) => {
                if (e.target === lightboxOverlay) {
                    this.closeLightbox();
                }
            });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.lightboxOpen) {
                switch(e.key) {
                    case 'Escape':
                        this.closeLightbox();
                        break;
                    case 'ArrowLeft':
                        this.navigateLightbox(-1);
                        break;
                    case 'ArrowRight':
                        this.navigateLightbox(1);
                        break;
                }
            }
        });
    }
    
    bindAdminFormEvents() {
        // File upload drag and drop
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('mediaFiles');
        
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.add('drag-over');
                });
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.remove('drag-over');
                });
            });
            
            uploadArea.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                this.handleFileSelection(files);
            });
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
        }
    }
    
    handleSearch(query) {
        this.searchQuery = query.toLowerCase();
        this.filterProfiles();
    }
    
    filterByCategory(category) {
        this.currentCategory = category;
        this.filterProfiles();
    }
    
    filterProfiles() {
        const profileCards = document.querySelectorAll('.profile-card');
        let visibleCount = 0;
        
        profileCards.forEach(card => {
            const title = card.querySelector('.profile-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.profile-subtitle')?.textContent.toLowerCase() || '';
            const categories = card.querySelector('.profile-categories')?.textContent.toLowerCase() || '';
            
            const matchesSearch = !this.searchQuery || 
                                title.includes(this.searchQuery) || 
                                description.includes(this.searchQuery) || 
                                categories.includes(this.searchQuery);
            
            const matchesCategory = this.currentCategory === 'all' || 
                                  categories.includes(this.currentCategory.toLowerCase());
            
            if (matchesSearch && matchesCategory) {
                card.style.display = 'block';
                card.classList.add('fade-in');
                visibleCount++;
            } else {
                card.style.display = 'none';
                card.classList.remove('fade-in');
            }
        });
        
        // Show/hide empty state
        this.toggleEmptyState(visibleCount === 0);
    }
    
    toggleEmptyState(show) {
        let emptyState = document.querySelector('.empty-state');
        
        if (show && !emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <h2>No models found</h2>
                <p>Try adjusting your search or category filter.</p>
            `;
            
            const profileGrid = document.getElementById('profileGrid');
            if (profileGrid) {
                profileGrid.insertAdjacentElement('afterend', emptyState);
            }
        } else if (!show && emptyState) {
            emptyState.remove();
        }
    }
    
    updateActiveCategoryBtn(activeBtn) {
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }
    
    initCategoryScroll() {
        const categoryBar = document.querySelector('.category-scroll');
        if (!categoryBar) return;
        
        let isDown = false;
        let startX;
        let scrollLeft;
        
        const handleMouseDown = (e) => {
            isDown = true;
            categoryBar.classList.add('active');
            startX = e.pageX - categoryBar.offsetLeft;
            scrollLeft = categoryBar.scrollLeft;
        };
        
        const handleMouseLeave = () => {
            isDown = false;
            categoryBar.classList.remove('active');
        };
        
        const handleMouseUp = () => {
            isDown = false;
            categoryBar.classList.remove('active');
        };
        
        const handleMouseMove = (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - categoryBar.offsetLeft;
            const walk = (x - startX) * 2;
            categoryBar.scrollLeft = scrollLeft - walk;
        };
        
        categoryBar.addEventListener('mousedown', handleMouseDown);
        categoryBar.addEventListener('mouseleave', handleMouseLeave);
        categoryBar.addEventListener('mouseup', handleMouseUp);
        categoryBar.addEventListener('mousemove', handleMouseMove);
        
        // Touch events for mobile
        categoryBar.addEventListener('touchstart', (e) => {
            startX = e.touches[0].pageX - categoryBar.offsetLeft;
            scrollLeft = categoryBar.scrollLeft;
        });
        
        categoryBar.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const x = e.touches[0].pageX - categoryBar.offsetLeft;
            const walk = (x - startX) * 2;
            categoryBar.scrollLeft = scrollLeft - walk;
        });
    }
    
    openLightbox(mediaList, startIndex = 0) {
        this.mediaItems = mediaList;
        this.currentMediaIndex = startIndex;
        this.lightboxOpen = true;
        
        this.updateLightboxContent();
        
        const lightboxOverlay = document.getElementById('lightboxOverlay');
        if (lightboxOverlay) {
            lightboxOverlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeLightbox() {
        this.lightboxOpen = false;
        
        const lightboxOverlay = document.getElementById('lightboxOverlay');
        if (lightboxOverlay) {
            lightboxOverlay.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        // Pause any playing videos
        const video = document.querySelector('#lightboxMedia video');
        if (video) {
            video.pause();
        }
    }
    
    navigateLightbox(direction) {
        if (this.mediaItems.length === 0) return;
        
        this.currentMediaIndex += direction;
        
        if (this.currentMediaIndex >= this.mediaItems.length) {
            this.currentMediaIndex = 0;
        } else if (this.currentMediaIndex < 0) {
            this.currentMediaIndex = this.mediaItems.length - 1;
        }
        
        this.updateLightboxContent();
    }
    
    updateLightboxContent() {
        const lightboxMedia = document.getElementById('lightboxMedia');
        const lightboxCounter = document.getElementById('lightboxCounter');
        
        if (!lightboxMedia || this.mediaItems.length === 0) return;
        
        const currentMedia = this.mediaItems[this.currentMediaIndex];
        lightboxMedia.innerHTML = '';
        
        if (currentMedia.type === 'image' || !currentMedia.type) {
            const img = document.createElement('img');
            img.src = currentMedia.src;
            img.alt = currentMedia.alt || 'Gallery image';
            img.className = 'lightbox-image';
            lightboxMedia.appendChild(img);
        } else if (currentMedia.type === 'video') {
            const video = document.createElement('video');
            video.src = currentMedia.src;
            video.controls = true;
            video.className = 'lightbox-video';
            lightboxMedia.appendChild(video);
        }
        
        if (lightboxCounter) {
            lightboxCounter.textContent = `${this.currentMediaIndex + 1} / ${this.mediaItems.length}`;
        }
    }
    
    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
    
    initInfiniteScroll() {
        // Placeholder for infinite scroll functionality
        // This would typically load more profiles as the user scrolls
        let loading = false;
        
        window.addEventListener('scroll', () => {
            if (loading) return;
            
            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
            
            if (scrollTop + clientHeight >= scrollHeight - 1000) {
                loading = true;
                // Load more profiles here
                setTimeout(() => {
                    loading = false;
                }, 1000);
            }
        });
    }
    
    preloadImages() {
        // Preload important images for better UX
        const profileImages = document.querySelectorAll('.profile-image');
        profileImages.forEach((img, index) => {
            if (index < 6) { // Preload first 6 images
                const preloadImg = new Image();
                preloadImg.src = img.src;
            }
        });
    }
    
    handleFileSelection(files) {
        const uploadPreview = document.getElementById('uploadPreview');
        const uploadArea = document.getElementById('uploadArea');
        
        if (!uploadPreview || !files.length) return;
        
        uploadPreview.innerHTML = '';
        uploadArea.style.display = 'none';
        
        Array.from(files).forEach((file, index) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            
            // Create thumbnail for images
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'preview-thumbnail';
                    previewItem.appendChild(img);
                };
                reader.readAsDataURL(file);
            } else if (file.type.startsWith('video/')) {
                const videoIcon = document.createElement('div');
                videoIcon.className = 'preview-video-icon';
                videoIcon.textContent = '🎥';
                previewItem.appendChild(videoIcon);
            }
            
            // File info
            const fileName = document.createElement('span');
            fileName.className = 'preview-filename';
            fileName.textContent = file.name;
            
            const fileSize = document.createElement('span');
            fileSize.className = 'preview-filesize';
            fileSize.textContent = this.formatFileSize(file.size);
            
            previewItem.appendChild(fileName);
            previewItem.appendChild(fileSize);
            uploadPreview.appendChild(previewItem);
        });
        
        // Add button to select more files
        const addMoreBtn = document.createElement('button');
        addMoreBtn.type = 'button';
        addMoreBtn.className = 'btn btn-secondary add-more-btn';
        addMoreBtn.textContent = 'Add More Files';
        addMoreBtn.addEventListener('click', () => {
            uploadArea.style.display = 'block';
            uploadPreview.innerHTML = '';
            document.getElementById('mediaFiles').value = '';
        });
        uploadPreview.appendChild(addMoreBtn);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, delay) {
        let timeoutId;
        let lastExecTime = 0;
        return function (...args) {
            const currentTime = Date.now();
            
            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.bootyMansion = new BootyMansion();
});

// Profile card click handlers (global function for template use)
function bindProfileCardEvents() {
    document.querySelectorAll('.profile-card').forEach(card => {
        card.addEventListener('click', () => {
            const profileId = card.dataset.profileId;
            if (profileId) {
                window.location.href = `/profile/${profileId}`;
            }
        });
    });
}

// Call this after dynamic content loading
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindProfileCardEvents);
} else {
    bindProfileCardEvents();
}