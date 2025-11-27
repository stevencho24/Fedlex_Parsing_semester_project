# Article Assignment Output

This folder contains the article assignment analysis results for Swiss law documents processed by the GPT_LLM_input_generator.

## Purpose

These files map legal cross-references to their specific article numbers, enabling automated legal analysis and relationship tracking between Swiss federal laws.

## Files

### 1. large_LLM_artikel_output_SR-611.01.json
**Document**: SR 611.01 - Verordnung zum Finanzhaushaltgesetz  
**Source**: GPT_Large_LLM_input_SR-611.01-01012026-DE.json  
**Items Analyzed**: 139

#### Statistics:
- **SR_link_detection**: 12 items
- **SR_link_with_local_acronym**: 1 item (DTI)
- **preamble_acronym**: 64 items (FHG references)
- **artikel_reference**: 62 items
- **Specific citations**: 133 (95.7%)
- **General references**: 6 (4.3%)

#### Most Cited Documents:
- SR 611.0 (Finanzhaushaltgesetz): 76 citations
- SR 611.01 (self-references): 48 citations
- SR 171.10 (Parlamentsgesetz): 4 citations

### 2. large_LLM_artikel_output_SR-725.11.json
**Document**: SR 725.11 - Bundesgesetz über die Nationalstrassen  
**Source**: GPT_Large_LLM_input_SR-725.11-01012023-DE.json  
**Items Analyzed**: 39

#### Statistics:
- **SR_link_detection**: 24 items
- **artikel_reference**: 15 items
- **Specific citations**: 29 (74.4%)
- **General references**: 10 (25.6%)

#### Most Cited Documents:
- SR 101 (Bundesverfassung): 7 citations
- SR 711 (Enteignungsgesetz): 7 citations
- SR 725.11 (self-references): 8 citations

### 3. large_LLM_artikel_output_SR-420.1.json
**Document**: SR 420.1 - Bundesgesetz über die Förderung der Forschung und der Innovation  
**Source**: GPT_Large_LLM_input_SR-420.1-01072023-DE.json  
**Items Analyzed**: 53

#### Highlights:
- Captures all explicit citations to SR 420.2 (Innosuisse-Gesetz), SR 414.20 (HFKG), SR 616.1 (Subventionsgesetz) and SR 313.0 (Verwaltungsstrafrecht)
- Distinguishes self-references (`artikel_reference`) that map inter-article dependencies within SR 420.1
- Handles article lists joined with “und” / commas in accordance with the contextual relationship rule set

### 4. large_LLM_artikel_output_SR-311.01.json
**Document**: SR 311.01 - Verordnung zum Strafgesetzbuch und zum Militärstrafgesetz  
**Source**: GPT_Large_LLM_input_SR-311.01-01072025-DE.json  
**Items Analyzed**: 81

#### Highlights:
- Resolves simultaneous references to StGB (SR 311.0), JStG (SR 311.1) and MStG (SR 321.0) using acronym logic
- Treats artikel_reference items that actually cite external statutes (e.g., “Art. 46 Abs. 1 StGB”) as outgoing SR references
- Consolidates self-references to SR 311.01 for internal dependency mapping

### 5. large_LLM_artikel_output_SR-531.11.json
**Document**: SR 531.11 - Verordnung über die wirtschaftliche Landesversorgung (VWLV)  
**Source**: GPT_Large_LLM_input_SR-531.11-01112025-DE.json  
**Items Analyzed**: 21

#### Highlights:
- Links LVG (SR 531) citations from both preamble-acronym and artikel_reference contexts, ensuring Art. 14, 16, 31, 46 LVG assignments remain consistent
- Captures auxiliary references to the Publikationsverordnung (SR 170.512.1), Handelsregisterverordnung (SR 221.411) and Obligationenrecht (SR 220)
- Distinguishes internal cross-references (e.g., Art. 7 Abs. 3 VWLV) from external statutory hooks

## Output Format

Each JSON file contains an array of items with the following structure:

```json
{
  "ITEM": 1,
  "ARTICLE_EID": "art_18",
  "item_type": "SR_link_detection",
  "TARGET_SR": "SR 170.512.1",
  "assigned_articles": ["Art. 20 Abs. 2"],
  "confidence": "high",
  "reasoning": "Explicit citation of Art. 20 Abs. 2 of SR 170.512.1"
}
```

### Fields:
- **ITEM**: Item number from source file
- **ARTICLE_EID**: Article identifier where citation appears
- **item_type**: Detection method (SR_link_detection, preamble_acronym, artikel_reference, SR_link_with_local_acronym)
- **TARGET_SR**: Target SR document being referenced
- **assigned_articles**: Array of article numbers assigned to this citation
- **confidence**: Confidence level (high, medium, low)
- **reasoning**: Explanation for the assignment
- **acronym** (optional): Local acronym detected
- **preamble_acronym** (optional): Preamble acronym name

## Item Types

### 1. SR_link_detection
Direct SR link citations found in the document. These represent explicit references to other Swiss laws.

**Example**: "gestützt auf das Parlamentsgesetz vom 13. Dezember 2002 SR 171.10"
- Assigns specific articles if mentioned in context
- Marks as "General reference - entire document" if no specific articles cited

### 2. SR_link_with_local_acronym
SR links accompanied by acronyms defined within the article (not in preamble).

**Example**: "(Bereich DTI)" followed by SR link
- Tracks acronym usage within the article
- Assigns specific articles from the citation

### 3. preamble_acronym
References to acronyms defined in the document preamble.

**Example**: "FHG" defined in preamble as Finanzhaushaltgesetz (SR 611.0)
- Implicit citations through acronym usage
- Extracts article numbers from context where acronym appears

### 4. artikel_reference
Cross-references to article numbers found in the text.

**Example**: "gemäss Artikel 22", "Art. 13-18"
- Can be internal (self) references or external
- Detected through pattern matching for "Art." or "Artikel"

## Confidence Levels

- **high**: Explicit citation with clear article numbers
- **medium**: Citation present but context ambiguous
- **low**: Reference detected but assignment uncertain

## Assignment Types

### Specific Article Citations
Examples:
- `["Art. 142 Abs. 2", "Art. 142 Abs. 3"]`
- `["Art. 20 Abs. 2"]`
- `["Art. 13–18"]` (ranges)

### General References
Examples:
- `["General reference - entire document"]`
- `["Self-reference - context unclear"]`

## Usage

These output files can be used for:

1. **Legal Relationship Mapping**: Visualize connections between Swiss laws
2. **Impact Analysis**: Determine which laws are affected by amendments
3. **Citation Validation**: Verify legal references are accurate
4. **LLM Training**: Provide structured data for legal AI models
5. **Research**: Analyze citation patterns in Swiss federal law

## Generation Date

- SR-611.01: November 12, 2024
- SR-725.11: November 12, 2024
- SR-420.1: November 16, 2025
- SR-311.01: November 17, 2025
- SR-531.11: November 19, 2025

## Next Steps

These article assignments can be used as input for:
- Legal knowledge graph construction
- Automated cross-reference validation
- LLM-based legal analysis
- Citation network visualization
- Impact assessment tools

## Notes

- Some references may be to historical law versions (e.g., Bundesrechtspflegegesetz now superseded by SR 173.110)
- Ranges like "Art. 13-18" may need expansion for detailed analysis
- Preamble acronyms create implicit citations throughout the document
- Self-references help track internal article dependencies


