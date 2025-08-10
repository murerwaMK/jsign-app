document.addEventListener('DOMContentLoaded', () => {
    const AppState = {
        currentDocId: null,
    };

    const DOM = {
        uploadModal: document.getElementById('upload-modal'),
        uploadModalBtn: document.getElementById('upload-modal-btn'),
        uploadForm: document.getElementById('upload-form'),
        docPreviewModal: document.getElementById('document-preview-modal'),
        closeBtns: document.querySelectorAll('.close-btn'),
        docGrid: document.getElementById('document-grid'),
        pendingList: document.getElementById('pending-list'),
        pendingSection: document.getElementById('pending-acknowledgments'),
        previewTitle: document.getElementById('preview-title'),
        docRenderArea: document.getElementById('document-render-area'),
        specialReqText: document.getElementById('special-requirements-text'),
        ackCheckbox: document.getElementById('ack-checkbox'),
        confirmAckBtn: document.getElementById('confirm-ack-btn'),
        ackStatusLists: document.getElementById('ack-status-lists'),
    };

    function init() {
        if (!DOM.docGrid) return;
        setupEventListeners();
        loadDocuments();
    }

    function setupEventListeners() {
        DOM.uploadModalBtn.addEventListener('click', () => DOM.uploadModal.style.display = 'block');
        DOM.closeBtns.forEach(btn => btn.onclick = () => btn.closest('.modal').style.display = 'none');
        DOM.uploadForm.addEventListener('submit', handleUpload);
        DOM.ackCheckbox.addEventListener('change', () => {
            DOM.confirmAckBtn.disabled = !DOM.ackCheckbox.checked;
        });
        DOM.confirmAckBtn.addEventListener('click', handleAcknowledge);
    }

    async function loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const data = await response.json();
            renderDocumentGrids(data.documents);
        } catch (error) {
            console.error('Failed to load documents:', error);
        }
    }

    function renderDocumentGrids(documents) {
        DOM.docGrid.innerHTML = '';
        DOM.pendingList.innerHTML = '';
        let pendingCount = 0;

        documents.forEach(doc => {
            const card = createDocumentCard(doc);
            DOM.docGrid.innerHTML += card;
            if (doc.status === 'Pending Acknowledgment') {
                pendingCount++;
                DOM.pendingList.innerHTML += card;
            }
        });
        DOM.pendingSection.style.display = pendingCount > 0 ? 'block' : 'none';
    }

    function createDocumentCard(doc) {
        const statusClass = doc.status.replace(/\s+/g, '-').toLowerCase();
        return `
            <div class="doc-card" onclick="App.openPreview(${doc.id})">
                <div class="doc-card-icon">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                </div>
                <div class="doc-card-body">
                    <h4>${doc.filename}</h4>
                    <p>Uploaded by: ${doc.uploader}</p>
                </div>
                <div class="doc-card-status ${statusClass}">${doc.status}</div>
            </div>
        `;
    }

    async function openPreview(docId) {
        AppState.currentDocId = docId;
        try {
            const response = await fetch(`/api/documents/${docId}`);
            const data = await response.json();
            
            DOM.previewTitle.textContent = data.filename;
            DOM.specialReqText.textContent = data.special_requirements;
            renderPdf(`/uploads/${data.filepath}`);

            // Render status lists
            DOM.ackStatusLists.innerHTML = `
                <div><h4>Acknowledged By:</h4><ul>${data.signed_by.map(u => `<li>${u.username}</li>`).join('')}</ul></div>
                <div><h4>Awaiting Acknowledgment:</h4><ul>${data.not_signed_by.map(u => `<li>${u.username}</li>`).join('')}</ul></div>
            `;

            DOM.ackCheckbox.checked = false;
            DOM.confirmAckBtn.disabled = true;
            DOM.docPreviewModal.style.display = 'block';
        } catch (error) {
            console.error('Failed to load document details:', error);
        }
    }

    async function renderPdf(url) {
        DOM.docRenderArea.innerHTML = '<p>Loading preview...</p>';
        pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/build/pdf.worker.min.js`;
        try {
            const pdf = await pdfjsLib.getDocument(url).promise;
            DOM.docRenderArea.innerHTML = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const viewport = page.getViewport({ scale: 1.2 });
                const canvas = document.createElement('canvas');
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
                DOM.docRenderArea.appendChild(canvas);
            }
        } catch (error) {
            DOM.docRenderArea.innerHTML = '<p>Sorry, could not display preview.</p>';
        }
    }

    async function handleUpload(e) {
        e.preventDefault();
        const formData = new FormData(DOM.uploadForm);
        const response = await fetch('/api/documents', { method: 'POST', body: formData });
        if (response.ok) {
            DOM.uploadModal.style.display = 'none';
            DOM.uploadForm.reset();
            loadDocuments();
        } else {
            alert('Upload failed.');
        }
    }

    async function handleAcknowledge() {
        if (!AppState.currentDocId) return;
        try {
            const response = await fetch(`/api/documents/${AppState.currentDocId}/sign`, { method: 'POST' });
            if (!response.ok) throw new Error('Acknowledgment failed.');
            DOM.docPreviewModal.style.display = 'none';
            loadDocuments();
        } catch (error) {
            alert(error.message);
        }
    }

    window.App = { openPreview };
    init();
});
// --- ADMIN DASHBOARD LOGIC ---
// Add this new code block to the end of your app.js file

document.addEventListener('DOMContentLoaded', () => {
    const createUserModal = document.getElementById('create-user-modal');
    const createUserBtn = document.getElementById('create-user-modal-btn');
    const editUserModal = document.getElementById('edit-user-modal');
    
    if (createUserBtn) {
        createUserBtn.onclick = () => {
            createUserModal.style.display = 'block';
        };
    }
    
    // Attach close functionality to any new modals
    document.querySelectorAll('.modal .close-btn').forEach(btn => {
        btn.onclick = () => {
            btn.closest('.modal').style.display = 'none';
        }
    });

    // Add function to global App object to be called from HTML
    if (window.App) {
        window.App.openEditUserModal = (userId, username, email, role) => {
            // Populate the form fields
            document.getElementById('edit-username').value = username;
            document.getElementById('edit-email').value = email;
            document.getElementById('edit-role').value = role;
            document.getElementById('edit-password').value = ''; // Clear password field

            // Set the form's action attribute to the correct URL
            const form = document.getElementById('edit-user-form');
            form.action = `/admin/users/${userId}/edit`;

            // Display the modal
            editUserModal.style.display = 'block';
        };
    }
});

// ADD THIS BLOCK TO THE END OF app.js

// This finds all the new edit buttons on the admin page and adds the correct click behavior
document.querySelectorAll('.edit-user-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Read the data from the data-* attributes
        const userId = button.dataset.userId;
        const username = button.dataset.username;
        const email = button.dataset.email;
        const role = button.dataset.role;
        
        // Call the function we already wrote to open the modal
        if (window.App && window.App.openEditUserModal) {
            window.App.openEditUserModal(userId, username, email, role);
        }
    });
});
// This code block is for the admin dashboard to handle user management