import json
import requests
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class BookGenerator:
    def __init__(self, ollama_host="127.0.0.1:11434", model="llama3.1:8b"):
        self.ollama_host = ollama_host
        self.model = model
        self.base_url = f"http://{ollama_host}/api/generate"
        
        # Book structure and memory
        self.book_structure = {}
        self.written_content = {}
        self.content_hashes = set()  # To track duplicate content
        self.current_progress = {}
        
        # Configuration for 8B model (higher capacity)
        self.words_per_page = 250  # Standard book page
        self.target_pages = 300
        self.target_words = self.words_per_page * self.target_pages
        self.chunk_size = 1200  # Larger chunks for 8B model
        self.max_context_length = 8192  # 8B model has larger context window
        
    def create_book_outline(self, topic: str) -> Dict:
        """Generate a comprehensive book outline for the given topic"""
        
        # Predefined structure templates for different topics
        structures = {
            "DevOps": {
    "Part I: Foundations of DevOps": {
        "Chapter 1: Operating Systems": [
            "Linux (RHEL, Ubuntu, SUSE)",
            "Unix (OpenBSD, FreeBSD, NetBSD)",
            "Windows"
        ],
        "Chapter 2: Terminals and Editors": [
            "Bash Scripting", 
            "PowerShell", 
            "Vim/Nano/Emacs", 
            "Learn to Live in Terminal"
        ],
        "Chapter 3: Programming Languages": [
            "Python", "Ruby", "JavaScript / Node.js", "Go", "Rust"
        ],
        "Chapter 4: Networking and Protocols": [
            "OSI Model", "DNS", "HTTP/HTTPS", "FTP/SFTP", 
            "SSL/TLS", "SSH", "Email Protocols (SMTP, IMAPS, POP3S)", 
            "DMARC", "SPF", "Domain Keys", "White/Grey Listing"
        ]
    },
    "Part II: Tools and Practices": {
        "Chapter 5: Version Control and Hosting": [
            "Git", "GitHub", "GitLab", "Bitbucket"
        ],
        "Chapter 6: Web Servers and Proxies": [
            "Apache", "Nginx", "Tomcat", "IIS",
            "Forward Proxy", "Reverse Proxy", "Firewall", "Load Balancer"
        ],
        "Chapter 7: Containers and Orchestration": [
            "Docker", "LXC", "Docker Swarm", "Kubernetes",
            "GKE/EKS/AKS", "AWS ECS / Fargate"
        ],
        "Chapter 8: CI/CD Tools": [
            "GitLab CI", "Jenkins", "GitHub Actions", "Travis CI",
            "CircleCI", "Drone", "TeamCity", "Azure DevOps Services"
        ],
        "Chapter 9: GitOps and Service Mesh": [
            "ArgoCD", "FluxCD",
            "Istio", "Consul", "Linkerd", "Envoy"
        ],
        "Chapter 10: Infrastructure as Code": [
            "Terraform", "AWS CDK", "Pulumi", "CloudFormation"
        ],
        "Chapter 11: Configuration Management": [
            "Ansible", "Chef", "Puppet"
        ]
    },
    "Part III: Monitoring and Management": {
        "Chapter 12: System Monitoring": [
            "Process Monitoring", "Performance Monitoring", 
            "Networking Tools"
        ],
        "Chapter 13: Infrastructure Monitoring": [
            "Datadog", "Grafana", "Zabbix", "Prometheus"
        ],
        "Chapter 14: Application Monitoring": [
            "Jaeger", "New Relic", "AppDynamics", "OpenTelemetry"
        ],
        "Chapter 15: Logs Management": [
            "Elastic Stack", "Graylog", "Splunk", 
            "Papertrail", "Loki"
        ],
        "Chapter 16: Artifact Management": [
            "Artifactory", "Nexus", "Cloudsmith"
        ],
        "Chapter 17: Secret Management": [
            "Vault", "Sealed Secrets", "SOPS"
        ]
    },
    "Part IV: Cloud and Serverless": {
        "Chapter 18: Cloud Providers": [
            "AWS", "Google Cloud", "Azure", "DigitalOcean",
            "Heroku", "Linode", "Vultr", "Alibaba Cloud"
        ],
        "Chapter 19: Serverless Platforms": [
            "Cloudflare", "AWS Lambda", "Azure Functions", 
            "GCP Functions", "Vercel", "Netlify"
        ],
        "Chapter 20: Cloud Design Patterns": [
            "Availability", "Data Management", 
            "Design and Implementation", "Management and Monitoring"
        ],
        "Chapter 21: Cloud Specific Tools": [
            "Cloud Specific Tools (General)"
        ]
    }
},
            "default": {
                "Part I: Introduction and Fundamentals": {
                    f"Chapter 1: Introduction to {topic.title()}": [
                        f"What is {topic.title()}?",
                        "Historical Context",
                        "Key Concepts and Terminology",
                        "Current State and Trends"
                    ],
                    f"Chapter 2: Theoretical Foundations": [
                        "Core Principles",
                        "Fundamental Theories",
                        "Research Methodologies",
                        "Interdisciplinary Connections"
                    ],
                    f"Chapter 3: Essential Skills and Tools": [
                        "Required Competencies",
                        "Software and Technologies",
                        "Best Practices",
                        "Learning Resources"
                    ]
                },
                "Part II: Core Concepts and Methods": {
                    f"Chapter 4: Primary Methodologies": [
                        "Approach 1: Traditional Methods",
                        "Approach 2: Modern Techniques",
                        "Comparative Analysis",
                        "Selection Criteria"
                    ],
                    f"Chapter 5: Advanced Techniques": [
                        "Cutting-edge Approaches",
                        "Emerging Technologies",
                        "Innovation Trends",
                        "Future Directions"
                    ],
                    f"Chapter 6: Practical Implementation": [
                        "Step-by-step Processes",
                        "Common Challenges",
                        "Solutions and Workarounds",
                        "Quality Assurance"
                    ]
                },
                "Part III: Applications and Case Studies": {
                    f"Chapter 7: Real-world Applications": [
                        "Industry Use Cases",
                        "Success Stories",
                        "Lessons Learned",
                        "ROI and Impact Measurement"
                    ],
                    f"Chapter 8: Case Study Analysis": [
                        "Detailed Case Study 1",
                        "Detailed Case Study 2",
                        "Comparative Analysis",
                        "Key Takeaways"
                    ],
                    f"Chapter 9: Specialized Domains": [
                        "Domain-specific Applications",
                        "Customization Strategies",
                        "Integration Challenges",
                        "Domain Expertise Requirements"
                    ]
                },
                "Part IV: Advanced Topics and Future": {
                    f"Chapter 10: Current Challenges": [
                        "Technical Limitations",
                        "Scalability Issues",
                        "Resource Constraints",
                        "Solution Strategies"
                    ],
                    f"Chapter 11: Future Trends": [
                        "Emerging Technologies",
                        "Market Predictions",
                        "Research Directions",
                        "Potential Disruptions"
                    ],
                    f"Chapter 12: Conclusion and Next Steps": [
                        "Summary of Key Points",
                        "Actionable Recommendations",
                        "Further Learning Paths",
                        "Final Thoughts"
                    ]
                }
            }
        }
   
        
        
        
                # Select appropriate structure
        # structure = structures.get(topic.lower().replace(" ", "_"), structures["default"])
        structure = structures.get(topic, structures["default"])

        
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
    
    def generate_content(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate content using Ollama API (optimized for 8B model)"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,  # Slightly higher for more creativity
                "top_p": 0.95,       # Higher for better quality
                "top_k": 40,         # Add top-k sampling
                "max_tokens": max_tokens,
                "repeat_penalty": 1.1,  # Reduce repetition
                "num_ctx": self.max_context_length  # Use full context window
            }
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=1000)
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
        """Create a context-aware prompt for content generation (optimized for 8B model)"""
        
        # Use larger context window for 8B model
        context_length = min(2000, len(previous_content))
        context_info = f"""
Previously written content summary:
{previous_content[-context_length:] if previous_content else "This is the beginning of the book."}

Book Structure Context:
- Topic: {topic}
- Current Part: {part}
- Current Chapter: {chapter}
- Current Section: {section['title']}
- Target Words: {section['target_words']}

Writing Guidelines:
- Write in an authoritative, engaging academic style
- Include specific examples, case studies, and practical applications
- Use proper headings and subheadings for organization
- Incorporate relevant statistics, research findings, and expert opinions
- Maintain consistency with the overall book narrative
- Ensure content is comprehensive and detailed for the target word count
"""
        
        prompt = f"""
You are an expert author writing a comprehensive, professional book about "{topic}". This book will be used as an authoritative reference by professionals, students, and researchers.

{context_info}

Write the section "{section['title']}" for the chapter "{chapter}".

Requirements:
- Write approximately {section['target_words']} words
- Be thorough, detailed, and comprehensive
- Include practical examples, code snippets, and real-world applications where relevant
- Use proper academic structure with clear subsections
- Incorporate current industry best practices and recent developments
- Maintain a professional yet accessible tone
- Include relevant statistics, research findings, and expert insights
- Ensure the content flows naturally from previous sections
- Do not repeat information already covered
- End with a smooth transition to prepare for the next section

Focus specifically on "{section['title']}" and provide in-depth coverage of this topic.

Section Content:
"""
        
        return prompt
    
    def generate_section(self, topic: str, part: str, chapter: str, section: Dict, 
                        previous_content: str = "") -> str:
        """Generate content for a specific section (optimized for 8B model)"""
        
        prompt = self.create_context_prompt(topic, part, chapter, section, previous_content)
        
        # 8B model can handle larger chunks, so generate in fewer iterations
        full_content = ""
        words_generated = 0
        target_words = section['target_words']
        max_iterations = 3  # Fewer iterations due to larger capacity
        
        for iteration in range(max_iterations):
            remaining_words = target_words - words_generated
            
            if remaining_words <= 100:  # Close enough to target
                break
                
            chunk_prompt = prompt
            
            if full_content:
                # Use larger context window for continuation
                context_window = min(1500, len(full_content))
                chunk_prompt += f"\n\nPrevious content from this section:\n{full_content[-context_window:]}\n\nContinue writing to reach approximately {remaining_words} more words. Build upon the previous content and maintain coherent flow:"
            else:
                chunk_prompt += f"\n\nBegin writing the section (target: {target_words} words):"
            
            # Generate larger chunks with 8B model
            chunk_content = self.generate_content(chunk_prompt, max_tokens=min(4096, remaining_words * 3))
            
            if not chunk_content or self.is_duplicate_content(chunk_content):
                print(f"    ⚠️  Iteration {iteration + 1}: No new content generated")
                break
            
            # Clean up the generated content
            chunk_content = self.clean_generated_content(chunk_content)
            
            full_content += "\n\n" + chunk_content if full_content else chunk_content
            words_generated = len(full_content.split())
            
            print(f"    📝 Iteration {iteration + 1}: {len(chunk_content.split())} words generated ({words_generated}/{target_words} total)")
            
            # Smaller delay for 8B model (it's more efficient)
            time.sleep(0.5)
            
            # Check if we've reached a good stopping point
            if words_generated >= target_words * 0.9:  # 90% of target is acceptable
                break
        
        return full_content
    
    def clean_generated_content(self, content: str) -> str:
        """Clean and format generated content"""
        # Remove common artifacts from generation
        content = content.strip()
        
        # Remove repetitive phrases that might occur
        lines = content.split('\n')
        cleaned_lines = []
        prev_line = ""
        
        for line in lines:
            line = line.strip()
            if line and line != prev_line:  # Remove duplicate consecutive lines
                cleaned_lines.append(line)
                prev_line = line
            elif line:  # Keep empty lines for formatting
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
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
    
    # Initialize the book generator for Llama 3.1 8B
    generator = BookGenerator(
        ollama_host="127.0.0.1:11434", 
        model="llama3.1:8b"
    )
    
    # Example usage
    topic = "DevOps"  # Change this to any topic you want
    
    print("🤖 AI Book Generator (Llama 3.1 8B Optimized)")
    print("=" * 60)
    print(f"Ollama Host: {generator.ollama_host}")
    print(f"Model: {generator.model}")
    print(f"Topic: {topic}")
    print(f"Target: {generator.target_pages} pages")
    print(f"Context Window: {generator.max_context_length} tokens")
    print(f"Chunk Size: {generator.chunk_size} words")
    
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
        print(f"   Model: Llama 3.1 8B")
        
    except KeyboardInterrupt:
        print("\n⏸️  Generation paused. Resume by running the script again.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure Ollama is running and llama3.1:8b model is available")

if __name__ == "__main__":
    main()