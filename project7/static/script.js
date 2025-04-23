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

    document.getElementById('runButton').addEventListener('click', function() {
        const requirements = Array.from(document.getElementsByName('requirement'))
            .map(input => input.value.trim())
            .filter(value => value !== '');
        
        console.log('Sending requirements:', requirements);
        
        if (requirements.length === 0) {
            document.getElementById('outputText').value = 'Please enter at least one requirement.';
            adjustTextareaHeight(document.getElementById('outputText'));
            return;
        }

        document.getElementById('outputText').value = 'Processing requirements...';
        adjustTextareaHeight(document.getElementById('outputText'));
        document.getElementById('referenceLinks').innerHTML = '';
        
        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ requirements: requirements })
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            
            const outputText = document.getElementById('outputText');
            if (data && data.output) {
                outputText.value = data.output;
                console.log('Setting output text to:', data.output);
            } else {
                outputText.value = 'No output received from server.';
                console.error('No output in response:', data);
            }
            adjustTextareaHeight(outputText);
            
            const linksContainer = document.getElementById('referenceLinks');
            linksContainer.innerHTML = '';
            if (data.references && data.references.length > 0) {
                data.references.forEach(link => {
                    const linkElement = document.createElement('div');
                    linkElement.innerHTML = `<a href="${link}" target="_blank">${link}</a>`;
                    linksContainer.appendChild(linkElement);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const outputText = document.getElementById('outputText');
            outputText.value = `Error: ${error.message}`;
            adjustTextareaHeight(outputText);
        });
    });
});
