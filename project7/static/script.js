// Theme toggle functionality
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Set initial theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// Function to auto-adjust textarea height
function adjustTextareaHeight(textarea) {
    if (textarea.id === 'outputText') {
        // For output textarea, allow full growth with proper spacing
        textarea.style.height = 'auto';
        const newHeight = Math.max(200, textarea.scrollHeight + 20); // Add extra padding
        textarea.style.height = newHeight + 'px';
    } else {
        // For input textareas, grow as needed
        textarea.style.height = 'auto';
        const newHeight = Math.max(2.5 * 16, textarea.scrollHeight);
        textarea.style.height = newHeight + 'px';
    }
}

// Add auto-adjust to all textareas
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('textarea').forEach(textarea => {
        // Set initial height
        adjustTextareaHeight(textarea);
        
        // Adjust on input
        textarea.addEventListener('input', function() {
            adjustTextareaHeight(this);
        });
    });

    document.getElementById('addRequirement').addEventListener('click', function() {
        const container = document.getElementById('requirementsContainer');
        const newBox = document.createElement('div');
        newBox.className = 'requirement-box';
        newBox.innerHTML = '<textarea name="requirement" placeholder="Enter your requirement here..." rows="1"></textarea>';
        container.appendChild(newBox);
        const newTextarea = newBox.querySelector('textarea');
        adjustTextareaHeight(newTextarea);
        
        // Add input event listener to new textarea
        newTextarea.addEventListener('input', function() {
            adjustTextareaHeight(this);
        });
    });

    document.getElementById('runButton').addEventListener('click', async function() {
        const requirements = Array.from(document.querySelectorAll('textarea[name="requirement"]'))
            .map(textarea => textarea.value)
            .filter(value => value.trim() !== '');

        if (requirements.length === 0) {
            alert('Please enter at least one requirement.');
            return;
        }

        // Show loading animation
        const loadingContainer = document.querySelector('.loading-container');
        const loadingText = document.querySelector('.loading-text');
        loadingContainer.style.display = 'block';

        // Start progress polling
        let progressInterval = setInterval(async () => {
            try {
                const response = await fetch('/progress');
                const data = await response.json();
                
                // Update loading text
                loadingText.textContent = data.task || 'Processing your research request...';
                
                // If progress is 100%, stop polling
                if (data.progress >= 100) {
                    clearInterval(progressInterval);
                }
            } catch (error) {
                console.error('Error fetching progress:', error);
            }
        }, 100); // Poll every 100ms

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ requirements: requirements })
            });

            const data = await response.json();
            
            // Clear the progress polling interval
            clearInterval(progressInterval);
            
            // Hide loading animation
            loadingContainer.style.display = 'none';
            
            // Update output
            document.getElementById('outputText').value = data.output;
            adjustTextareaHeight(document.getElementById('outputText'));
            
            // Extract sources from the output text
            const outputText = data.output;
            const sources = [];
            
            // Look for sources in the format <sources>...</sources>
            if (outputText.includes('<sources>') && outputText.includes('</sources>')) {
                const sourcesText = outputText.split('<sources>')[1].split('</sources>')[0];
                sources.push(...sourcesText.split('\n').map(s => s.trim()).filter(s => s));
            }
            
            // Update reference links
            const referenceLinks = document.getElementById('referenceLinks');
            referenceLinks.innerHTML = '';
            
            if (sources.length > 0) {
                // Add sources from the output
                sources.forEach(link => {
                    const a = document.createElement('a');
                    a.href = link;
                    a.textContent = link;
                    a.target = '_blank';
                    a.rel = 'noopener noreferrer';
                    referenceLinks.appendChild(a);
                    referenceLinks.appendChild(document.createElement('br'));
                });
            } else {
                // Add a message if no sources are found
                const noSources = document.createElement('p');
                noSources.textContent = 'No reference links available';
                noSources.style.color = 'var(--text-color)';
                noSources.style.opacity = '0.7';
                referenceLinks.appendChild(noSources);
            }
            
            // Add any additional references from the API response
            if (data.references && data.references.length > 0) {
                data.references.forEach(link => {
                    if (!sources.includes(link)) {  // Avoid duplicates
                        const a = document.createElement('a');
                        a.href = link;
                        a.textContent = link;
                        a.target = '_blank';
                        a.rel = 'noopener noreferrer';
                        referenceLinks.appendChild(a);
                        referenceLinks.appendChild(document.createElement('br'));
                    }
                });
            }
        } catch (error) {
            console.error('Error:', error);
            clearInterval(progressInterval);
            loadingContainer.style.display = 'none';
            alert('An error occurred while processing your request.');
        }
    });

    document.getElementById('trashButton').addEventListener('click', function() {
        document.getElementById('outputText').value = '';
        document.getElementById('referenceLinks').innerHTML = '';
        adjustTextareaHeight(document.getElementById('outputText'));
    });

    document.getElementById('saveButton').addEventListener('click', function() {
        // Show the save modal
        const modal = document.getElementById('saveModal');
        modal.style.display = 'block';
        
        // Focus the title input
        const titleInput = document.getElementById('saveTitle');
        
        // Get the first requirement as the title
        const requirements = Array.from(document.querySelectorAll('textarea[name="requirement"]'))
            .map(textarea => textarea.value)
            .filter(value => value.trim() !== '');
        
        if (requirements.length > 0) {
            // Use the first requirement as the title
            const title = requirements[0].substring(0, 50) + (requirements[0].length > 50 ? '...' : '');
            titleInput.value = title;
        }
        
        titleInput.focus();
    });

    // Handle save confirmation
    document.getElementById('confirmSave').addEventListener('click', function() {
        const titleInput = document.getElementById('saveTitle');
        const title = titleInput.value.trim();
        
        if (!title) {
            alert('Please enter a title for your research');
            return;
        }
        
        const requirements = Array.from(document.querySelectorAll('textarea[name="requirement"]'))
            .map(textarea => textarea.value)
            .filter(value => value.trim() !== '');
        
        const output = document.getElementById('outputText').value;
        const references = Array.from(document.getElementById('referenceLinks').children)
            .filter(link => link.tagName === 'A')  // Only get actual links, not <br> elements
            .map(link => link.href);
        
        fetch('/save_output', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                requirements: requirements,
                content: output,
                references: references
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Hide the modal
                document.getElementById('saveModal').style.display = 'none';
                // Clear only the title input
                titleInput.value = '';
                // Don't clear output or reference links
                // Refresh only the left panel to show the new saved output
                const leftPanel = document.querySelector('.left-notes');
                fetch(window.location.href)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newLeftPanel = doc.querySelector('.left-notes');
                        leftPanel.innerHTML = newLeftPanel.innerHTML;
                    });
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Handle save cancellation
    document.getElementById('cancelSave').addEventListener('click', function() {
        document.getElementById('saveModal').style.display = 'none';
        document.getElementById('saveTitle').value = '';
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('saveModal');
        if (event.target === modal) {
            modal.style.display = 'none';
            document.getElementById('saveTitle').value = '';
        }
    });
});

function adjustNoteHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

function addNoteBox() {
    const notesContainer = document.getElementById('notesContainer');
    const newNoteBox = document.createElement('div');
    newNoteBox.className = 'note-box';
    
    const textarea = document.createElement('textarea');
    textarea.className = 'note-input';
    textarea.placeholder = '';
    textarea.rows = 1;
    
    // Add input event listener for auto-resize
    textarea.addEventListener('input', function() {
        adjustNoteHeight(this);
    });
    
    newNoteBox.appendChild(textarea);
    notesContainer.appendChild(newNoteBox);
}

// Add auto-resize to existing note textareas
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.note-input').forEach(textarea => {
        textarea.addEventListener('input', function() {
            adjustNoteHeight(this);
        });
    });
});

function clearAllSaved() {
    if (confirm('Are you sure you want to delete all saved research pages? This cannot be undone.')) {
        fetch('/clear_saved', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
    }
}