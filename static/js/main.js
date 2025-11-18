// API Base URL
const API_BASE = '/api';

// Global state
let allSubdomains = [];
let filteredSubdomains = [];

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalSubdomains').textContent = data.stats.total_subdomains;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load all subdomains
async function loadSubdomains() {
    try {
        const response = await fetch(`${API_BASE}/subdomains`);
        const data = await response.json();
        
        if (data.success) {
            allSubdomains = data.subdomains;
            filteredSubdomains = [...allSubdomains];
            renderSubdomains();
        }
    } catch (error) {
        console.error('Error loading subdomains:', error);
        showError('Failed to load subdomains');
    }
}

// Render subdomains table
function renderSubdomains() {
    const tbody = document.getElementById('subdomainsTableBody');
    
    if (filteredSubdomains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No subdomains found</td></tr>';
        return;
    }
    
    tbody.innerHTML = filteredSubdomains.map(sub => `
        <tr class="fade-in">
            <td><strong>${sub.subdomain}</strong></td>
            <td><span class="badge badge-primary">${sub.tld.toUpperCase()}</span></td>
            <td><code>${sub.target}</code></td>
            <td>${sub.ssl_enabled ? '✅ Yes' : '❌ No'}</td>
            <td><span class="badge ${sub.status === 'active' ? 'badge-success' : 'badge-danger'}">${sub.status}</span></td>
            <td>${formatDate(sub.created_at)}</td>
            <td class="action-buttons">
                <button class="icon-btn" onclick="editSubdomain('${sub.subdomain}', '${sub.tld}')" title="Edit">
                    ✏️
                </button>
                <button class="icon-btn" onclick="deleteSubdomainConfirm('${sub.subdomain}', '${sub.tld}')" title="Delete">
                    🗑️
                </button>
                <button class="icon-btn" onclick="viewSubdomain('${sub.subdomain}', '${sub.tld}')" title="View">
                    👁️
                </button>
            </td>
        </tr>
    `).join('');
}

// Search subdomains
function searchSubdomains() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    
    filteredSubdomains = allSubdomains.filter(sub => 
        sub.subdomain.toLowerCase().includes(query) ||
        sub.tld.toLowerCase().includes(query) ||
        sub.target.toLowerCase().includes(query)
    );
    
    filterSubdomains();
}

// Filter subdomains
function filterSubdomains() {
    const tldFilter = document.getElementById('tldFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    let filtered = [...filteredSubdomains];
    
    if (tldFilter) {
        filtered = filtered.filter(sub => sub.tld === tldFilter);
    }
    
    if (statusFilter) {
        filtered = filtered.filter(sub => sub.status === statusFilter);
    }
    
    filteredSubdomains = filtered;
    renderSubdomains();
}

// Modal functions
function openCreateModal() {
    document.getElementById('createModal').classList.add('active');
}

function closeCreateModal() {
    document.getElementById('createModal').classList.remove('active');
    document.getElementById('createSubdomainForm').reset();
    document.getElementById('createResult').className = 'result-message';
}

function openEditModal() {
    document.getElementById('editModal').classList.add('active');
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    document.getElementById('editSubdomainForm').reset();
    document.getElementById('editResult').className = 'result-message';
}

// Create subdomain
async function createSubdomain(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        subdomain: formData.get('subdomain').toLowerCase(),
        tld: formData.get('tld'),
        target: formData.get('target'),
        record_type: formData.get('recordType'),
        ssl_enabled: formData.get('sslEnabled') === 'on'
    };
    
    const resultDiv = document.getElementById('createResult');
    resultDiv.className = 'result-message';
    resultDiv.textContent = 'Creating subdomain...';
    resultDiv.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/subdomains`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.className = 'result-message success';
            resultDiv.textContent = '✅ Subdomain created successfully!';
            form.reset();
            setTimeout(() => {
                closeCreateModal();
                loadSubdomains();
                loadStats();
            }, 2000);
        } else {
            resultDiv.className = 'result-message error';
            resultDiv.textContent = `❌ Error: ${result.error}`;
        }
    } catch (error) {
        console.error('Error creating subdomain:', error);
        resultDiv.className = 'result-message error';
        resultDiv.textContent = '❌ Failed to create subdomain';
    }
}

// Edit subdomain
function editSubdomain(subdomain, tld) {
    const subdomainData = allSubdomains.find(s => s.subdomain === subdomain && s.tld === tld);
    
    if (!subdomainData) return;
    
    document.getElementById('editSubdomain').value = subdomain;
    document.getElementById('editTld').value = tld;
    document.getElementById('editFullDomain').textContent = `${subdomain}.${tld}`;
    document.getElementById('editTarget').value = subdomainData.target;
    document.getElementById('editStatus').value = subdomainData.status;
    document.getElementById('editSslEnabled').checked = subdomainData.ssl_enabled;
    
    openEditModal();
}

// Update subdomain
async function updateSubdomain(event) {
    event.preventDefault();
    
    const form = event.target;
    const subdomain = document.getElementById('editSubdomain').value;
    const tld = document.getElementById('editTld').value;
    
    const data = {
        target: document.getElementById('editTarget').value,
        status: document.getElementById('editStatus').value,
        ssl_enabled: document.getElementById('editSslEnabled').checked
    };
    
    const resultDiv = document.getElementById('editResult');
    resultDiv.className = 'result-message';
    resultDiv.textContent = 'Updating subdomain...';
    resultDiv.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/subdomains/${tld}/${subdomain}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.className = 'result-message success';
            resultDiv.textContent = '✅ Subdomain updated successfully!';
            setTimeout(() => {
                closeEditModal();
                loadSubdomains();
            }, 2000);
        } else {
            resultDiv.className = 'result-message error';
            resultDiv.textContent = `❌ Error: ${result.error}`;
        }
    } catch (error) {
        console.error('Error updating subdomain:', error);
        resultDiv.className = 'result-message error';
        resultDiv.textContent = '❌ Failed to update subdomain';
    }
}

// Delete subdomain
function deleteSubdomainConfirm(subdomain, tld) {
    if (confirm(`Are you sure you want to delete ${subdomain}.${tld}?`)) {
        deleteSubdomain(subdomain, tld);
    }
}

async function deleteSubdomain(subdomain, tld) {
    try {
        const response = await fetch(`${API_BASE}/subdomains/${tld}/${subdomain}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Subdomain deleted successfully!');
            loadSubdomains();
            loadStats();
        } else {
            showError(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error deleting subdomain:', error);
        showError('Failed to delete subdomain');
    }
}

// View subdomain
function viewSubdomain(subdomain, tld) {
    const subdomainData = allSubdomains.find(s => s.subdomain === subdomain && s.tld === tld);
    
    if (!subdomainData) return;
    
    const info = `
Subdomain: ${subdomain}
TLD: ${tld}
Full Domain: ${subdomain}.${tld}
Target: ${subdomainData.target}
Record Type: ${subdomainData.record_type}
SSL Enabled: ${subdomainData.ssl_enabled ? 'Yes' : 'No'}
Status: ${subdomainData.status}
Created: ${formatDate(subdomainData.created_at)}
Updated: ${formatDate(subdomainData.updated_at)}
    `;
    
    alert(info);
}

// Create subdomain for specific TLD
function createSubdomainForTLD(tld) {
    openCreateModal();
    document.getElementById('tld').value = tld;
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showSuccess(message) {
    // You can implement a toast notification here
    alert(`✅ ${message}`);
}

function showError(message) {
    // You can implement a toast notification here
    alert(`❌ ${message}`);
}

function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const createModal = document.getElementById('createModal');
    const editModal = document.getElementById('editModal');
    
    if (event.target === createModal) {
        closeCreateModal();
    }
    if (event.target === editModal) {
        closeEditModal();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadSubdomains();
});
