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

- `XML_scraper.py` - Advanced XML parser for Swiss law documents in AkomaNtoso format
- `simple_scraper.py` - Basic scraper using requests + BeautifulSoup
- `requirements.txt` - Python dependencies
- `landesrecht_sections.json` - Landesrecht section mappings
- `main_section.json` - Main section mappings
- `swiss_law_articles.json` - Parsed articles output
- `swiss_law_articles.html` - HTML output for articles
- `SR-*.xml` - Sample Swiss law XML documents

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the XML scraper
python XML_scraper.py

# Run the simple scraper
python simple_scraper.py
```

## Features

### Advanced XML Scraper (`XML_scraper.py`)
- **AkomaNtoso Format Support**: Parses Swiss law documents in the official AkomaNtoso XML format
- **Hierarchical Storage**: Automatically categorizes articles by Landesrecht and Main Section based on document numbers
- **Enhanced Text Extraction**: Extracts clean article text without duplication, excluding authorialNote content
- **ref_articles Functionality**: Collects article references between authorialNote tags for hyperlink context
- **SR Category URL Filtering**: Only saves URLs with `eli/cc/` structure (Swiss legal documents)
- **Multiple Output Formats**: Generates both JSON and HTML outputs
- **Comprehensive Metadata**: Extracts document numbers, titles, dates, and hierarchical paths

### Basic Scraper (`simple_scraper.py`)
- Uses requests + BeautifulSoup (no browser required)
- Fallback to mock data if website scraping fails
- Lightweight and easy to run
- Extracts chapter numbers and titles into a structured dictionary
- Comprehensive error handling and logging

## Output Format

### XML Scraper Output
The XML scraper generates structured article data:
```json
{
  "article_id": "901.022.2_art_5",
  "hierarchical_storage": [
    "Landesrecht: Wirtschaft - Technische Zusammenarbeit",
    "Main Section: Regionalpolitik"
  ],
  "document_number": "901.022.2",
  "document_title": "Verordnung des WBF über die Gewährung von Steuererleichterungen im Rahmen der Regionalpolitik",
  "article_number": "Art. 5",
  "article_title": "Lehrstellen und Personalverleih",
  "article_text": "Lehrstellen werden als Arbeitsplätze angerechnet...",
  "hyperlinks": [
    {
      "url": "https://fedlex.data.admin.ch/eli/cc/1991/408_408_408",
      "text": "SR 823.111",
      "target_document": "SR 1991.408_408_408",
      "ref_articles": ["27"]
    }
  ],
  "article_url": "https://www.fedlex.admin.ch/eli/cc/2016/350/de#art_5",
  "document_home_url": "https://www.fedlex.admin.ch/eli/cc/2016/350/de"
}
```

### Simple Scraper Output
The simple scraper generates section mappings:
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
- xml.etree.ElementTree (built-in)
- requests
- beautifulsoup4
- lxml

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Usage Examples

### XML Scraper Usage
```python
from XML_scraper import SwissLawXMLScraper

# Initialize scraper
scraper = SwissLawXMLScraper()

# Parse XML file
articles = scraper.parse_xml_file('SR-901.022.2-01072016-DE.xml')

# Print summary
scraper.print_articles_summary()

# Save to JSON and HTML
scraper.save_articles_to_json()
scraper.save_articles_to_html()
```

### Simple Scraper Usage
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

## Current Status

The project has successfully implemented:

✅ **XML Parsing**: Complete AkomaNtoso XML document parsing  
✅ **Hierarchical Storage**: Automatic categorization by document numbers  
✅ **Text Extraction**: Clean article text without duplication  
✅ **ref_articles**: Contextual article reference collection  
✅ **URL Filtering**: SR category URL filtering (`eli/cc/` structure)  
✅ **Multiple Documents**: Support for SR-613.11, SR-721.101, SR-901.022.2  
✅ **Output Formats**: JSON and HTML generation  

## Troubleshooting

### Website Access Issues
If the scraper doesn't work:
1. Check your internet connection
2. Verify the website is accessible
3. The scraper will fall back to mock data if needed

### XML Parsing Issues
If XML parsing fails:
1. Check XML file format and encoding
2. Verify AkomaNtoso namespace declarations
3. Check for malformed XML elements

### No Sections Found
If no sections are found:
1. The website structure may have changed
2. The scraper will fall back to mock data
3. Check the logs for specific error messages

## Next Steps

This scraper provides the foundation for:
1. Extracting subsections and sub-subsections
2. Downloading XML files for each section
3. Parsing the hierarchical structure (Titel → Kapitel → Article → Paragraph)
4. Building a comprehensive Swiss law database
5. Training LLMs on Swiss legal language and structure
6. Automated legal change detection and impact analysis

## License

This project is for educational and research purposes. Please respect the Swiss federal law website's terms of service and robots.txt file.
