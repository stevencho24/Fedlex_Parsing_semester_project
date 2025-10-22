# Swiss Law XML Parsing Project

This project aims to scrape and parse Swiss federal law documents from the official [fedlex.admin.ch](https://www.fedlex.admin.ch/de/home?news_period=last_day&news_pageNb=1&news_order=desc&news_itemsPerPage=10) website, specifically focusing on the Landesrecht (National Law) sections.

## Project Context and Motivation

### Swiss Legal System Digital Infrastructure
Swiss laws are stored digitally on the official federal law website at [fedlex.admin.ch](https://www.fedlex.admin.ch/de/home?news_period=last_day&news_pageNb=1&news_order=desc&news_itemsPerPage=10). This digital repository serves as the central hub for accessing all federal legal documents in Switzerland.

### Organizational Structure
The legal documents are organized in a hierarchical structure with multiple levels:

1. **Main Sections**: The website contains various broad categories of legal content
2. **Systematic Collection of Laws**: Within the main sections, there is a specific "systematic collection of laws" section that serves as our primary focus
3. **Landesrecht (National Law)**: Within the systematic collection, we focus specifically on the "Landesrecht" section, accessible at [fedlex.admin.ch/de/cc/internal-law/1](https://www.fedlex.admin.ch/de/cc/internal-law/1)

### Landesrecht Structure
The Landesrecht page displays a clear hierarchical organization:

- **Left Panel**: Navigation menu showing main sections (e.g., "1 Staat - Volk - Behörden", "2 Privatrecht - Zivilrechtspflege - Vollstreckung", etc.)
- **Right Panel**: Detailed content area showing subsections and sub-subsections within the selected main section
- **Interactive Elements**: Each subsection and sub-subsection is clickable, leading to XML files containing the complete legal text

### Legal Document Hierarchy
Swiss legal documents follow a specific hierarchical structure for organization:

1. **Titel** (Title) - Top-level organizational unit
2. **Kapitel** (Chapter) - Subdivision within a Titel
3. **Article** - Specific legal provisions within a Kapitel
4. **Paragraph** - Numbered subsections within an Article
5. **Letters** - Further subdivisions within paragraphs

This structure ensures consistent organization across all Swiss legal documents, making them systematically navigable and referenceable.

### Project Motivation

#### Uncharted Territory in Legal Tech
Swiss law XML documents have not been systematically parsed for machine processing before. This represents a significant opportunity to pioneer automated legal document analysis in the Swiss legal system.

#### Comprehensive Data Extraction Goals
The project aims to accurately parse Swiss legal documents by extracting:

- **Location Metadata**: Precise storage location including:
  - Landesrecht section classification
  - Subsection identification
  - Sub-subsection categorization
  - Complete hierarchical path through the legal system

- **Content Structure**: Detailed parsing of legal content including:
  - **Titel** information and context
  - **Kapitel** organization and scope
  - **Article numbers** and their legal significance
  - **Text content** within each section
  - **Hyperlinks** connecting to other articles of law

#### LLM Training and Legal Change Detection
The ultimate goal is to leverage this parsed legal data to:

1. **Train Large Language Models (LLMs)**: Feed the structured legal data into machine learning models to understand Swiss legal language, structure, and relationships
2. **Automated Legal Change Detection**: Enable LLMs to automatically identify affected laws when changes occur, providing:
   - Real-time impact assessment
   - Cross-reference analysis
   - Legal compliance monitoring
   - Automated legal research assistance

#### Potential Impact
This project could revolutionize how legal professionals, researchers, and citizens interact with Swiss law by:
- Enabling sophisticated legal search and analysis
- Automating the identification of legal implications when laws change
- Creating a foundation for AI-powered legal assistance tools
- Improving access to legal information through better search and discovery mechanisms

## Project Structure

- `simple_scraper.py` - Main scraper using requests + BeautifulSoup
- `requirements.txt` - Python dependencies
- `landesrecht_sections.json` - Output: Scraped sections (generated)
- `landesrecht_sections.txt` - Output: Human-readable sections (generated)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python simple_scraper.py
```

## Features

### Main Scraper (`simple_scraper.py`)
- Uses requests + BeautifulSoup (no browser required)
- Fallback to mock data if website scraping fails
- Lightweight and easy to run
- Extracts chapter numbers and titles into a structured dictionary
- Comprehensive error handling and logging

## Output Format

The scrapers generate a dictionary with the following structure:
```python
{
    "1": "Staat - Volk - Behörden",
    "2": "Privatrecht - Zivilrechtspflege - Vollstreckung",
    "3": "Strafrecht - Strafrechtspflege - Strafvollzug",
    # ... more sections
}
```

## Expected Landesrecht Sections

Based on the Swiss legal system, the scraper should extract these main sections:

1. **Staat - Volk - Behörden** (State - People - Authorities)
2. **Privatrecht - Zivilrechtspflege - Vollstreckung** (Private Law - Civil Justice - Enforcement)
3. **Strafrecht - Strafrechtspflege - Strafvollzug** (Criminal Law - Criminal Justice - Execution)
4. **Schule - Wissenschaft - Kultur** (School - Science - Culture)
5. **Landesverteidigung** (National Defense)
6. **Finanzen** (Finances)
7. **Öffentliche Werke - Energie - Verkehr** (Public Works - Energy - Transport)
8. **Gesundheit - Arbeit - Soziale Sicherheit** (Health - Labor - Social Security)
9. **Wirtschaft - Technische Zusammenarbeit** (Economy - Technical Cooperation)

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Usage Examples

### Basic Usage
```python
from simple_scraper import SimpleSwissLawScraper

# Initialize scraper
scraper = SimpleSwissLawScraper()

# Scrape sections
sections = scraper.scrape_landesrecht_sections()

# Print results
scraper.print_sections()

# Save to file
scraper.save_sections_to_file("my_sections.json")
```

## Troubleshooting

### Website Access Issues
If the scraper doesn't work:
1. Check your internet connection
2. Verify the website is accessible
3. The scraper will fall back to mock data if needed

### No Sections Found
If no sections are found:
1. The website structure may have changed
2. The scraper will fall back to mock data
3. Check the logs for specific error messages

## MUST DO WITH EVERY QUERY

When working on this project, follow these mandatory steps for every code change or enhancement:

### 1. Understanding and Analysis
- **Explain your understanding of the query and why the user wants to make these changes**
  - Clearly articulate what the user is asking for
  - Identify the underlying motivation and goals
  - Understand the context within the broader Swiss law parsing project

### 2. Current Implementation Assessment
- **Explain why the current implementation is lacking regards to the query**
  - Identify specific gaps or limitations in the existing code
  - Explain what needs to be improved or added
  - Highlight any architectural or design issues

### 3. Clarification and Edge Cases
- **Double check and clarify any ambiguities and edge cases with the user's query**
  - Ask clarifying questions about requirements
  - Identify potential edge cases and error scenarios
  - Confirm assumptions about data formats, error handling, etc.
  - **IMPORTANT: All clarifying questions must be answered before any coding takes place**

### 4. Code Documentation
- **Input comments into each line of code and explain what exactly it does**
  - Add comprehensive inline comments
  - Explain the purpose of each function, class, and method
  - Document parameters, return values, and side effects
  - Include examples where helpful

### 5. Code Quality Assurance
- **Ensure with every line of code, there is no redundancy in implementation/variables**
  - Remove duplicate code and unused variables
  - Optimize algorithms and data structures
  - Ensure consistent naming conventions
  - Validate error handling and edge cases

### 6. Implementation Explanation
- **After the edits explain step by step with line number references what the new code achieves**
  - Provide a detailed walkthrough of the changes
  - Reference specific line numbers and code sections
  - Explain how the new implementation addresses the original query
  - Highlight any improvements or optimizations made

## Next Steps

This scraper provides the foundation for:
1. Extracting subsections and sub-subsections
2. Downloading XML files for each section
3. Parsing the hierarchical structure (Titel → Kapitel → Article → Paragraph)
4. Building a comprehensive Swiss law database

## License

This project is for educational and research purposes. Please respect the Swiss federal law website's terms of service and robots.txt file.
