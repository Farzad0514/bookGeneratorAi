import json
import requests
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import course_content  # Assuming this is a module with predefined book structures

class BookGenerator:
    def __init__(self, ollama_host="127.0.0.1:11434", model="llama3.2:1b"):
        self.ollama_host = ollama_host
        self.model = model
        self.base_url = f"http://{ollama_host}/api/generate"
        
        # Book structure and memory
        self.book_structure = {}
        self.written_content = {}
        self.content_hashes = set()  # To track duplicate content
        self.current_progress = {}
        
        # Configuration
        self.words_per_page = 250  # Standard book page
        self.target_pages = 300
        self.target_words = self.words_per_page * self.target_pages
        self.chunk_size = 500  # Words per generation chunk
        
    def create_book_outline(self, topic: str) -> Dict:
        """Generate a comprehensive book outline for the given topic"""
        
        # Predefined structure templates for different topics
        structures = course_content.structure
        # Select appropriate structure
        structure = structures.get(topic.lower().replace(" ", "_"), structures["structure"])
        
        # Calculate word allocation
        total_sections = sum(len(sections) for part in structure.values() for sections in part.values())
        words_per_section = self.target_words // total_sections
        
        # Add word targets to structure
        for part_name, chapters in structure.items():
            for chapter_name, sections in chapters.items():
                for i, section in enumerate(sections):
                    structure[part_name][chapter_name][i] = {
                        "title": section,
                        "target_words": words_per_section,
                        "status": "pending"
                    }
        
        return structure
    
    def generate_content(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate content using Ollama API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": max_tokens
            }
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating content: {e}")
            return ""
    
    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is duplicate using hash comparison"""
        content_hash = hashlib.md5(content.lower().strip().encode()).hexdigest()
        
        if content_hash in self.content_hashes:
            return True
        
        self.content_hashes.add(content_hash)
        return False
    
    def create_context_prompt(self, topic: str, part: str, chapter: str, section: Dict, 
                            previous_content: str = "") -> str:
        """Create a context-aware prompt for content generation"""
        
        context_info = f"""
Previously written content summary:
{previous_content[-500:] if previous_content else "This is the beginning of the book."}

Book Structure Context:
- Topic: {topic}
- Current Part: {part}
- Current Chapter: {chapter}
- Current Section: {section['title']}
- Target Words: {section['target_words']}
"""
        
        prompt = f"""
You are writing a comprehensive book about "{topic}". 

{context_info}

Write the section "{section['title']}" for the chapter "{chapter}".

Requirements:
- Write approximately {section['target_words']} words
- Be detailed, informative, and engaging
- Include practical examples and explanations
- Maintain academic rigor while being accessible
- Do not repeat information from previous sections
- Focus specifically on "{section['title']}"
- Include relevant code examples if applicable
- Structure with clear subsections and paragraphs

Section Content:
"""
        
        return prompt
    
    def generate_section(self, topic: str, part: str, chapter: str, section: Dict, 
                        previous_content: str = "") -> str:
        """Generate content for a specific section"""
        
        prompt = self.create_context_prompt(topic, part, chapter, section, previous_content)
        
        # Generate content in chunks to manage token limits
        full_content = ""
        words_generated = 0
        target_words = section['target_words']
        
        while words_generated < target_words:
            remaining_words = target_words - words_generated
            chunk_prompt = prompt + f"\n\nContinue writing (need approximately {remaining_words} more words):\n"
            
            if full_content:
                chunk_prompt += f"\n\nPrevious content:\n{full_content[-300:]}\n\nContinue from where you left off:"
            
            chunk_content = self.generate_content(chunk_prompt, max_tokens=min(2000, remaining_words * 2))
            
            if not chunk_content or self.is_duplicate_content(chunk_content):
                break
            
            full_content += "\n\n" + chunk_content if full_content else chunk_content
            words_generated = len(full_content.split())
            
            # Small delay to avoid overwhelming the API
            time.sleep(1)
        
        return full_content
    
    def save_progress(self, filename: str):
        """Save current progress to file"""
        progress_data = {
            "book_structure": self.book_structure,
            "written_content": self.written_content,
            "current_progress": self.current_progress,
            "content_hashes": list(self.content_hashes),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self, filename: str):
        """Load previous progress from file"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                
            self.book_structure = progress_data.get("book_structure", {})
            self.written_content = progress_data.get("written_content", {})
            self.current_progress = progress_data.get("current_progress", {})
            self.content_hashes = set(progress_data.get("content_hashes", []))
            
            print(f"Progress loaded from {filename}")
            return True
        return False
    
    def generate_book(self, topic: str, resume: bool = True):
        """Generate the complete book"""
        
        progress_file = f"{topic.lower().replace(' ', '_')}_book_progress.json"
        output_file = f"{topic.lower().replace(' ', '_')}_book.md"
        
        # Load previous progress if resuming
        if resume:
            self.load_progress(progress_file)
        
        # Create or load book structure
        if not self.book_structure:
            print(f"Creating book outline for '{topic}'...")
            self.book_structure = self.create_book_outline(topic)
            print("Book outline created!")
        
        print(f"\nGenerating book: '{topic.title()}'")
        print(f"Target: {self.target_pages} pages ({self.target_words} words)")
        print("=" * 60)
        
        total_sections = sum(len(sections) for part in self.book_structure.values() 
                           for sections in part.values())
        completed_sections = 0
        
        # Generate content section by section
        previous_content = ""
        
        for part_name, chapters in self.book_structure.items():
            print(f"\n📚 {part_name}")
            
            for chapter_name, sections in chapters.items():
                print(f"  📖 {chapter_name}")
                
                for section_idx, section in enumerate(sections):
                    section_key = f"{part_name}|{chapter_name}|{section_idx}"
                    
                    # Skip if already completed
                    if section_key in self.written_content:
                        print(f"    ✓ {section['title']} (already completed)")
                        completed_sections += 1
                        continue
                    
                    print(f"    ⏳ Writing: {section['title']}")
                    
                    # Generate section content
                    content = self.generate_section(topic, part_name, chapter_name, 
                                                  section, previous_content)
                    
                    if content:
                        self.written_content[section_key] = {
                            "title": section['title'],
                            "content": content,
                            "word_count": len(content.split()),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        previous_content += f"\n\n{content}"
                        completed_sections += 1
                        
                        print(f"    ✅ Completed: {len(content.split())} words")
                    else:
                        print(f"    ❌ Failed to generate content")
                    
                    # Save progress periodically
                    if completed_sections % 5 == 0:
                        self.save_progress(progress_file)
                        self.save_book_to_file(topic, output_file)
                    
                    # Progress update
                    progress = (completed_sections / total_sections) * 100
                    print(f"    Progress: {completed_sections}/{total_sections} ({progress:.1f}%)")
        
        # Final save
        self.save_progress(progress_file)
        self.save_book_to_file(topic, output_file)
        
        print(f"\n🎉 Book generation completed!")
        print(f"📄 Book saved as: {output_file}")
        print(f"💾 Progress saved as: {progress_file}")
        
        return output_file
    
    def save_book_to_file(self, topic: str, filename: str):
        """Save the complete book to a markdown file"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Title page
            f.write(f"# {topic.title()}: A Comprehensive Guide\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write("---\n\n")
            
            # Table of contents
            f.write("## Table of Contents\n\n")
            for part_name, chapters in self.book_structure.items():
                f.write(f"### {part_name}\n")
                for chapter_name, sections in chapters.items():
                    f.write(f"- {chapter_name}\n")
                    for section in sections:
                        f.write(f"  - {section['title']}\n")
                f.write("\n")
            
            f.write("---\n\n")
            
            # Book content
            total_words = 0
            
            for part_name, chapters in self.book_structure.items():
                f.write(f"# {part_name}\n\n")
                
                for chapter_name, sections in chapters.items():
                    f.write(f"## {chapter_name}\n\n")
                    
                    for section_idx, section in enumerate(sections):
                        section_key = f"{part_name}|{chapter_name}|{section_idx}"
                        
                        f.write(f"### {section['title']}\n\n")
                        
                        if section_key in self.written_content:
                            content = self.written_content[section_key]['content']
                            f.write(f"{content}\n\n")
                            total_words += len(content.split())
                        else:
                            f.write("*[Content pending generation]*\n\n")
                    
                    f.write("---\n\n")
            
            # Statistics
            f.write(f"\n## Book Statistics\n\n")
            f.write(f"- **Total Words**: {total_words:,}\n")
            f.write(f"- **Estimated Pages**: {total_words // self.words_per_page}\n")
            f.write(f"- **Completion**: {len(self.written_content)} sections\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")

# Usage example and main execution
def main():
    """Main function to demonstrate usage"""
    
    # Initialize the book generator
    generator = BookGenerator(
        ollama_host="127.0.0.1:11434", 
        model="llama3.1:8b"
    )
    
    # Example usage
    topic = "DevOps"  # Change this to any topic you want
    
    print("🤖 AI Book Generator")
    print("=" * 50)
    print(f"Ollama Host: {generator.ollama_host}")
    print(f"Model: {generator.model}")
    print(f"Topic: {topic}")
    print(f"Target: {generator.target_pages} pages")
    
    try:
        # Generate the book (with resume capability)
        output_file = generator.generate_book(topic, resume=True)
        
        print(f"\n✅ Success! Book saved as: {output_file}")
        
        # Display final statistics
        total_words = sum(content['word_count'] for content in generator.written_content.values())
        estimated_pages = total_words // generator.words_per_page
        
        print(f"\n📊 Final Statistics:")
        print(f"   Words: {total_words:,}")
        print(f"   Pages: {estimated_pages}")
        print(f"   Sections: {len(generator.written_content)}")
        
    except KeyboardInterrupt:
        print("\n⏸️  Generation paused. Resume by running the script again.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()