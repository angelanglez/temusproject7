import os 
from flask import Flask, session, render_template, request, jsonify, send_from_directory
from datetime import datetime
import json
import uuid
from research import ResearchPipeline
import threading
import time

app = Flask(__name__)
app.secret_key = b'\xc5\x8f\xbc\xa2\x1d\xeb\xb3\x94;:d\x03'

# Directory to store saved pages
SAVED_PAGES_DIR = 'saved_pages'

# Ensure the directory exists
os.makedirs(SAVED_PAGES_DIR, exist_ok=True)

# Variables for LLM integration
research_question = []
research_answer = """test output."""
researcher = ResearchPipeline()  # Initialize the research pipeline
research_sources = []

# Progress tracking
current_progress = 0
progress_lock = threading.Lock()
current_task = ""
research_results = {"output": "", "sources": []}  # Store research results
stage_durations = {
    "init": 2,        # 2 seconds
    "plan": 5,        # 5 seconds
    "start_research": 2,  # 2 seconds
    "research": 20,   # 15 seconds per point
    "start_write": 2, # 2 seconds
    "write": 10,      # 10 seconds
    "finalize": 3     # 3 seconds
}

def update_progress(progress, task=""):
    global current_progress, current_task
    with progress_lock:
        current_progress = progress
        current_task = task

def reset_progress():
    global current_progress, current_task, research_results
    with progress_lock:
        current_progress = 0
        current_task = ""
        research_results = {"output": "", "sources": []}

@app.route('/progress', methods=['GET'])
def get_progress():
    with progress_lock:
        return jsonify({
            'progress': current_progress,
            'task': current_task
        })

llmLinks = []  # Test links, will be replaced with actual LLM links

def get_saved_pages():
    """Get list of all saved pages"""
    pages = []
    for filename in os.listdir(SAVED_PAGES_DIR):
        if filename.endswith('.html'):
            file_path = os.path.join(SAVED_PAGES_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract title from the file content
                title_start = content.find('<title>') + 7
                title_end = content.find('</title>')
                if title_start > 7 and title_end > title_start:
                    title = content[title_start:title_end].strip()
                else:
                    # Fallback to filename without extension
                    title = filename[:-5]
                
                # Get file creation time
                created_at = datetime.fromtimestamp(os.path.getctime(file_path))
                
                pages.append({
                    'id': filename[:-5],  # Remove .html extension
                    'title': title,
                    'created_at': created_at
                })
    
    # Sort by creation time, newest first
    return sorted(pages, key=lambda x: x['created_at'], reverse=True)

def get_next_sequence_number():
    """Get the next sequence number for saved pages"""
    pages = get_saved_pages()
    if not pages:
        return 1
    
    # Extract numbers from titles like "Research #1", "Research #2", etc.
    numbers = []
    for page in pages:
        title = page['title']
        if title.startswith("Research #"):
            try:
                num = int(title.split("#")[1])
                numbers.append(num)
            except (ValueError, IndexError):
                pass
    
    return max(numbers) + 1 if numbers else 1

@app.route('/', methods=['GET'])
def index():
    saved_pages = get_saved_pages()
    return render_template(
        "index.html",
        title="Project 7 - Research Helper",
        saved_outputs=saved_pages
    )

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        query = data.get('requirements', [])
        print("Received data:", data)  # Debug print
        
        if not data or 'requirements' not in data:
            return jsonify({
                'output': 'Error: Invalid request format',
                'references': []
            }), 400

        requirements = data.get('requirements', [])
        print("Requirements:", requirements)  # Debug print
        
        # Store inputs for LLM processing
        research_question = requirements
        
        # Process the research question using the research pipeline
        try:
            # Join the requirements into a single query string
            query = " ".join(requirements)
            
            # Reset progress before starting
            reset_progress()
            
            # Create a thread for the research process
            def research_thread():
                try:
                    # Stage 1/7: Initializing (0-14%)
                    update_progress(14, "Initializing research process...")
                    
                    # Stage 2/7: Planning research outline (14-28%)
                    update_progress(28, "Planning research outline...")
                    outline = researcher.plan(query)
                    
                    # Stage 3/7: Starting evidence gathering (28-42%)
                    update_progress(42, "Starting evidence gathering...")
                    evidence = {}
                    
                    # Stage 4/7: Gathering evidence for each point (42-70%)
                    for i, bullet in enumerate(outline):
                        progress = 42 + (i / len(outline) * 28)  # 42% to 70%
                        update_progress(int(progress), f"Researching point {i+1}/{len(outline)}...")
                        evidence[bullet] = researcher.research(bullet)
                    
                    # Stage 5/7: Starting final report (70-84%)
                    update_progress(84, "Writing final report...")
                    
                    # Stage 6/7: Writing report (84-98%)
                    result = researcher.write(query, outline, evidence)
                    update_progress(98, "Finalizing report...")
                    
                    # Stage 7/7: Extracting sources and completing (98-100%)
                    sources = []
                    if "<sources>" in result and "</sources>" in result:
                        sources_text = result.split("<sources>")[1].split("</sources>")[0]
                        sources = [s.strip() for s in sources_text.split("\n") if s.strip()]
                    
                    update_progress(100, "Research complete!")
                    
                    # Store results in the global variable
                    with progress_lock:
                        research_results["output"] = result
                        research_results["sources"] = sources
                    
                except Exception as e:
                    print(f"Error in research thread: {str(e)}")
                    update_progress(0, f"Error: {str(e)}")
                    with progress_lock:
                        research_results["output"] = f"Error processing research: {str(e)}"
                        research_results["sources"] = []
            
            # Start the research thread
            thread = threading.Thread(target=research_thread)
            thread.start()
            
            # Wait for the thread to complete
            thread.join()
            
            # Get the results from the global variable
            with progress_lock:
                output = research_results["output"]
                references = research_results["sources"]
            
        except Exception as e:
            print(f"Error in research pipeline: {str(e)}")
            output = f"Error processing research: {str(e)}"
            references = []
        
        response = {
            'output': output,
            'references': references
        }
        print("Sending response:", response)  # Debug print
        
        return jsonify(response)
    except Exception as e:
        print("Error:", str(e))  # Debug print
        return jsonify({
            'output': f'Error processing request: {str(e)}',
            'references': []
        }), 500

@app.route('/save_output', methods=['POST'])
def save_output():
    try:
        data = request.get_json()
        
        # Generate a unique ID for the page
        page_id = str(uuid.uuid4())
        
        # Use the title from the modal
        title = data.get('title', 'Untitled Research')
        
        # Create the HTML content
        html_content = render_template(
            'saved_output.html',
            output={
                'id': page_id,
                'title': title,
                'requirements': data['requirements'],
                'content': data['content'],
                'references': data['references'],
                'created_at': datetime.now()
            },
            saved_outputs=get_saved_pages()
        )
        
        # Save the HTML file
        file_path = os.path.join(SAVED_PAGES_DIR, f"{page_id}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({'success': True, 'id': page_id})
    except Exception as e:
        print("Error saving output:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/view_saved/<id>', methods=['GET'])
def view_saved(id):
    file_path = os.path.join(SAVED_PAGES_DIR, f"{id}.html")
    
    if not os.path.exists(file_path):
        return "Output not found", 404
    
    # Read the HTML file
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/delete_output/<id>', methods=['DELETE'])
def delete_output(id):
    try:
        file_path = os.path.join(SAVED_PAGES_DIR, f"{id}.html")
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': True})
    except Exception as e:
        print("Error deleting output:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear_saved', methods=['DELETE'])
def clear_saved():
    try:
        # Get all files in the saved_pages directory
        for filename in os.listdir(SAVED_PAGES_DIR):
            if filename.endswith('.html'):
                file_path = os.path.join(SAVED_PAGES_DIR, filename)
                os.remove(file_path)
        return jsonify({'success': True})
    except Exception as e:
        print("Error clearing saved pages:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
  
# Run in VSCode terminal:
# ./run.sh