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
- `GPT_LLM_input_generator.py` - Context extraction for LLM-based article assignment
- `simple_scraper.py` - Basic scraper using requests + BeautifulSoup
- `requirements.txt` - Python dependencies
- `landesrecht_sections.json` - Landesrecht section mappings
- `main_section.json` - Main section mappings
- `swiss_law_articles.json` - Parsed articles output
- `swiss_law_articles.html` - HTML output for articles
- `GPT_Large_LLM_input_725-11.json` - Generated LLM input with contextual article references
- `SR-*.xml` - Sample Swiss law XML documents

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the XML scraper
python XML_scraper.py

# Run the simple scraper
python simple_scraper.py

# NEW: Automated article assignment (XML → JSON → Article Assignments)
python3 automated_article_assignment.py SR-420.1-01072023-DE.xml
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

### LLM Input Generator (`GPT_LLM_input_generator.py`)

This module extracts contextual information from Swiss law XML documents to create pre-trimmed JSON files for Large Language Model (LLM) processing. The goal is to provide semantic context that allows an LLM to accurately assign article values to legal cross-references.

### Automated Article Assignment Pipeline (`automated_article_assignment.py`)

**NEW**: This automation script streamlines the entire workflow from XML parsing to article assignment in a single command. It combines the LLM input generator with automated article assignment logic based on syntactic and semantic analysis rules.

**Usage:**
```bash
python3 automated_article_assignment.py <XML_FILE>

# Example:
python3 automated_article_assignment.py SR-420.1-01072023-DE.xml
```

**What it does:**
1. Runs `GPT_LLM_input_generator.py` on your XML file
2. Automatically analyzes the generated JSON for article assignments
3. Applies contextual relationship analysis (syntactic + semantic)
4. Generates the final `large_LLM_artikel_output_<SR-number>.json` file

**Key Features:**
- **One-command execution**: No need to run multiple scripts manually
- **Automated SR detection**: Extracts SR number from filename for proper self-reference handling
- **Contextual analysis**: Applies prepositional attribution, direct marking, and isolation detection
- **Smart article extraction**: Handles complex article formats (ranges, subsections, etc.)
- **Comprehensive output**: Includes confidence levels and reasoning for each assignment

#### Motivation
Swiss legal documents contain complex cross-references between laws, articles, and subsections. Traditional parsing struggles with:
- **Semantic ambiguity**: SR links may cite entire documents without specifying which articles
- **Acronym resolution**: Legal abbreviations require context to resolve
- **Hierarchical references**: References can be to the same document or external documents
- **Implicit citations**: Some references are implied through acronyms defined elsewhere

The LLM Input Generator creates a structured context file that captures all necessary information for an LLM to resolve these ambiguities accurately.

#### Robustness Features

##### SR Link Detection from Multiple Attributes
Swiss law XML documents use different attributes to store SR document links. To ensure comprehensive detection:

**Dual Attribute Checking**: The generator checks both `href` and `fedlex:rs-uri` attributes for SR links.
- **Pattern**: Uses `/eli/cc/` pattern to identify valid Swiss legal document links
- **Flexibility**: Protocol and domain agnostic - works regardless of `http://` vs `https://` or domain variations
- **Namespace Handling**: Tries multiple methods to access `fedlex:rs-uri`:
  1. With namespace: `{http://fedlex.admin.ch/}rs-uri`
  2. Without namespace: `fedlex:rs-uri`
  3. Attribute dictionary iteration for any attribute containing `rs-uri`

**Why This Matters**: Some XML entries use `href` for taxonomy/classification links while storing the actual SR document link in `fedlex:rs-uri`. By checking both attributes, we ensure no SR references are missed.

**Example XML Patterns Handled**:
```xml
<!-- Pattern 1: SR link in href -->
<ref href="https://fedlex.data.admin.ch/eli/cc/2016/227">SR 611.0</ref>

<!-- Pattern 2: SR link in fedlex:rs-uri, taxonomy link in href -->
<ref 
  fedlex:rs-uri="https://fedlex.data.admin.ch/eli/cc/2016/712"
  href="https://fedlex.data.admin.ch/vocabulary/legal-taxonomy/6877">
  SR 420.2
</ref>
```

**Duplicate Handling**: If both attributes contain `/eli/cc/` links, both are processed. The natural deduplication logic (based on SNIPPET and ARTICLE_EID) will filter out true duplicates while preserving distinct references.

#### Detection Methodologies

##### 1. **Preamble Callback (`preamble_callback`)**
**Purpose**: Establish a reference dictionary of acronyms defined in the preamble with their associated SR links.

**Methodology**:
- Scans the preamble for single-word acronyms in parentheses (e.g., "(FHG)")
- Excludes acronyms nested within `<authorialNote>` tags
- Locates all `<authorialNote>` elements containing SR links (eli/cc URLs)
- Associates each acronym with the nearest SR link by element position
- Creates a callback item listing all preamble acronyms with their SR links

**Why This Matters**: 
Preamble acronyms are document-level definitions that are referenced throughout the entire legal document. Providing this upfront allows the LLM to understand that mentions of "FHG" throughout the document refer to "SR 611.0" without needing to re-analyze each occurrence.

**Edge Cases Handled**:
- Acronyms in element `.tail` (text after closing tags)
- Multiple SR links with varying distances from acronyms
- Duplicate acronym definitions (only first occurrence used)

##### 2. **SR Link Detection (`SR_link_detection`)**
**Purpose**: Capture standard legal citations with their full paragraph context.

**Methodology**:
- Iterates through all `<authorialNote>` elements in the document
- Extracts `<ref>` elements with `href` starting with `https://fedlex.data.admin.ch/eli/cc`
- Determines context (article or preamble) by traversing parent elements
- Extracts the complete paragraph containing the citation (from `<content><p>` tags)
- Excludes text from other `<authorialNote>` elements in the same paragraph
- Includes the current `<authorialNote>` text in the snippet

**Why This Matters**:
The full paragraph provides semantic context about WHY the SR link is cited, which helps the LLM understand the relationship between documents and determine which specific articles are relevant.

**Edge Cases Handled**:
- Citations in preambles (captured as `ARTICLE_EID: "preamble"`)
- Multiple SR links in the same paragraph (each gets its own item)
- Nested paragraph structures (prefers `<content>` as paragraph boundary)

##### 3. **SR Link with Local Acronym (`SR_link_with_local_acronym`)**
**Purpose**: Track acronyms defined within specific articles (not in preamble) and where they're referenced.

**Methodology**:
- Detects all-caps abbreviations (2+ letters) immediately preceding `<authorialNote>` elements
- Supports acronyms with or without parentheses (e.g., "DTI" or "(DTI)")
- Searches the article for all subsequent mentions of the acronym
- Extracts specific lines containing the acronym (excluding `<authorialNote>` content)
- Only searches within `<content>` elements at leaf-level tags (`p`, `item`, `listIntroduction`, `subheading`)

**Why This Matters**:
Local acronyms provide article-specific context. When "DTI" is defined in article 18, knowing where it's mentioned later in that same article helps the LLM understand the scope and relevance of the citation.

**Edge Cases Handled**:
- Acronyms with special characters (e.g., "I/O", "A-B")
- Hierarchical element duplication (only extracts from leaf-level elements)
- Article title vs. content distinction (excludes titles)

##### 4. **Preamble Acronym References (`preamble_acronym`)**
**Purpose**: Detect when preamble-defined acronyms are referenced in articles and capture the context.

**Methodology**:
- Uses the preamble acronym dictionary from the callback
- Scans all elements in each article (excluding `<authorialNote>` content)
- Searches both element `.text` and `.tail` for acronym mentions
- Collects all contexts within the same article where the acronym appears
- Combines multiple contexts into a single snippet with "..." separators
- Creates one JSON item per article per preamble acronym

**Why This Matters**:
When "FHG" (defined in preamble as SR 611.0) is mentioned in article 27, the LLM needs to know that this reference implicitly cites SR 611.0. The combined contexts show all places where the implicit citation is relevant.

**Edge Cases Handled**:
- Multiple references to the same acronym in one article (combined into one item)
- References in subheadings, list items, and paragraphs
- Avoiding duplication with explicit SR links in `<authorialNote>`

##### 5. **Artikel References (`artikel_reference`)**
**Purpose**: Capture cross-references to other articles within the same or related documents.

**Methodology**:
- Pattern matching for "Art. ##" or "Artikel ##" with optional letters (e.g., "Art. 27b")
- Only searches within `<content>` elements (excludes article titles/headings)
- Restricts to leaf-level elements (`p`, `item`, `listIntroduction`, `subheading`)
- Excludes any text within `<authorialNote>` elements
- Deduplicates against existing snippets from other detection methods
- Creates one item per unique line containing an article reference

**Why This Matters**:
Article cross-references indicate relationships between legal provisions. "See Artikel 27b" tells the LLM that the current article depends on or relates to another specific article, which is crucial for semantic article assignment.

**Edge Cases Handled**:
- Sub-articles with letters (27a, 27b, 30a)
- Article ranges (Art. 13–18)
- Hierarchical duplication (parent `<content>` vs. child `<p>`)
- Overlap with other detection methods (prevents duplicate snippets)

#### Leaf-Level Element Strategy

To avoid hierarchical duplication, the generator only extracts text from specific "leaf-level" elements:
- `<p>` - Paragraph text
- `<item>` - List items
- `<listIntroduction>` - List introductory text
- `<subheading>` - Section subheadings

This ensures that if "Artikel 27b" appears in a `<p>` tag within an `<item>` tag within a `<content>` tag, it's only extracted once from the most specific element (`<p>`), not three times.

#### Output Structure

Each detection method produces JSON items with consistent structure:

```json
{
  "item_type": "SR_link_detection",
  "ITEM": 5,
  "ARTICLE_EID": "art_18",
  "TARGET_SR": "SR 611.0",
  "TARGET_URL": "https://fedlex.data.admin.ch/eli/cc/2006/227",
  "SNIPPET": "Full paragraph context...",
  "INSIDE_AUTHORIALNOTE": "Text within the authorialNote"
}
```

Special fields by item type:
- `preamble_callback`: `acronyms` array with `{acronym, sr_link, url}`
- `SR_link_with_local_acronym`: `acronym`, `snippet_acronym` array
- `preamble_acronym`: `preamble_acronym_name`
- `artikel_reference`: No URL or TARGET_SR fields

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

## LLM Article Assignment Prompt

### Purpose
The generated JSON file (e.g., `GPT_Large_LLM_input_725-11.json`) provides all necessary context for an LLM to assign specific article numbers to SR link citations. Many Swiss legal citations reference entire documents (e.g., "SR 611.0") without specifying which articles within that document are relevant. The LLM's task is to analyze the context and determine the appropriate article assignments.

### Prompt Template

```
You are a legal document analyst specializing in Swiss federal law (Systematische Rechtssammlung).

TASK: Analyze the provided JSON file containing Swiss law cross-references and assign specific article numbers to each SR link citation based on context.

INPUT FILE: [filename].json

STRUCTURE:
The JSON file contains items with 5 different detection methods (item_type):

1. preamble_callback: Reference dictionary of acronyms defined in the preamble
   - Contains: acronym name, sr_link, url
   - Use this to understand document-level acronym definitions

2. SR_link_detection: Standard SR link citations with paragraph context
   - Contains: ARTICLE_EID, TARGET_SR, TARGET_URL, SNIPPET, INSIDE_AUTHORIALNOTE
   - The SNIPPET shows the full paragraph where the citation appears
   - INSIDE_AUTHORIALNOTE shows the exact citation text

3. SR_link_with_local_acronym: SR links with article-specific acronyms
   - Contains all fields from SR_link_detection plus:
     - acronym: The abbreviation defined in this article
     - snippet_acronym: Where the acronym is mentioned in the article
   - Use snippet_acronym to understand the scope of the acronym's usage

4. preamble_acronym: Implicit citations via preamble acronyms
   - Contains: ARTICLE_EID, TARGET_SR (from preamble), SNIPPET, preamble_acronym_name
   - The article references the preamble acronym without an explicit SR link
   - Treat these as implicit citations to the TARGET_SR document

5. artikel_reference: Cross-references to other articles
   - Contains: ARTICLE_EID, SNIPPET (just the line with "Art. ##")
   - These indicate relationships between articles
   - May reference articles within the same document or implicitly to cited documents

ASSIGNMENT RULES:

1. CONTEXT ANALYSIS:
   - Read the SNIPPET carefully to understand WHY the SR link is cited
   - Look for specific article numbers mentioned near the citation (e.g., "Art. 29 FHG")
   - Consider the legal topic being discussed in the paragraph

2. EDGE CASE: Citations Without Article Numbers
   - Some citations reference entire documents: "gestützt auf das Finanzhaushaltgesetz vom 7. Oktober 2005 SR 611.0 (FHG)"
   - If no specific article is mentioned in the context, assign: "General reference - entire document"
   - If the context implies multiple articles, list them: ["Art. 13", "Art. 14", "Art. 15"]

3. EDGE CASE: Self-References
   - artikel_reference items often cite articles within the SAME document
   - Check if the referenced article number matches other ARTICLE_EID values in the file
   - If it's a self-reference, note: "Internal reference within current document"

4. EDGE CASE: Acronym-Based Citations
   - preamble_acronym items are implicit citations through acronyms
   - Example: "Art. 2 FHG" in article text, where FHG = SR 611.0
   - Extract the article number from the SNIPPET where the acronym appears
   - Format: "Art. 2" (of SR 611.0)

5. EDGE CASE: Article Ranges
   - Some citations reference ranges: "Art. 13–18 FHG"
   - Assign as: ["Art. 13", "Art. 14", "Art. 15", "Art. 16", "Art. 17", "Art. 18"]
   - Or as a range string: "Art. 13-18"

6. COMBINED REFERENCES:
   - snippet_acronym in SR_link_with_local_acronym shows where the acronym is used
   - Use this to identify related article references
   - Example: If snippet_acronym contains "gemäss Art. 30a", assign "Art. 30a"

7. DISAMBIGUATION:
   - Multiple SR links may cite the same document
   - Use the specific context (SNIPPET) to distinguish which articles each refers to
   - Each JSON item should get its own independent article assignment

OUTPUT FORMAT:
For each item in the JSON (except preamble_callback), provide:

{
  "ITEM": [item number],
  "ARTICLE_EID": [source article],
  "TARGET_SR": [target document],
  "assigned_articles": [list of article numbers or "General reference - entire document"],
  "confidence": [high/medium/low],
  "reasoning": [brief explanation of your assignment]
}

EXAMPLE:
Given this item:
{
  "item_type": "preamble_acronym",
  "ARTICLE_EID": "art_27_a",
  "TARGET_SR": "SR 611.0",
  "SNIPPET": "ausserordentliche Einnahmen und Ausgaben nach den Artikeln 13 Absatz 2 und 15 FHG.",
  "preamble_acronym_name": "FHG"
}

Your response:
{
  "ITEM": "N/A",
  "ARTICLE_EID": "art_27_a",
  "TARGET_SR": "SR 611.0",
  "assigned_articles": ["Art. 13 Abs. 2", "Art. 15"],
  "confidence": "high",
  "reasoning": "Snippet explicitly mentions 'Artikeln 13 Absatz 2 und 15 FHG'. Clear reference to specific articles."
}

SPECIAL INSTRUCTIONS:
- Process all items systematically
- Use the preamble_callback as a reference dictionary throughout
- Cross-reference artikel_reference items with SR links to identify implicit connections
- If context is ambiguous, mark confidence as "low" and explain why
- Be conservative: if no articles are clearly indicated, use "General reference - entire document"
```

### Usage Example

```bash
# Generate the JSON input file (input file is required)
python3 GPT_LLM_input_generator.py SR-611.01-01012026-DE.xml

# Output file is automatically named based on input file:
# Input:  SR-611.01-01012026-DE.xml
# Output: GPT_Large_LLM_input_SR-611.01-01012026-DE.json

# If no input file is provided, the script will show usage and exit:
# python3 GPT_LLM_input_generator.py
# Usage: python3 GPT_LLM_input_generator.py <XML_FILE>

# Provide the JSON file and prompt to your LLM
# (OpenAI API, Claude, Gemini, etc.)

# The LLM will output article assignments for each citation
```

### Expected LLM Capabilities

The LLM should be able to:
- **Semantic understanding**: Interpret legal German text to identify implicit article references
- **Pattern recognition**: Recognize article citation patterns like "Art. 13 Abs. 2", "Artikel 27b", "Art. 13–18"
- **Context integration**: Use information from multiple JSON items to resolve ambiguous references
- **Acronym resolution**: Apply preamble acronym mappings consistently throughout the document
- **Cross-referencing**: Identify when artikel_reference items relate to SR link citations

## License

This project is for educational and research purposes. Please respect the Swiss federal law website's terms of service and robots.txt file.
