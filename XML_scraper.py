#!/usr/bin/env python3
"""
XML Scraper for Swiss Law Documents
Parses AkomaNtoso XML format to extract individual articles with metadata
"""

import xml.etree.ElementTree as ET
import json
import re
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SwissLawXMLScraper:
    """Scraper for parsing Swiss law XML documents in AkomaNtoso format"""
    
    def __init__(self):
        self.namespaces = {
            'akn': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0',
            'fedlex': 'http://fedlex.admin.ch/'
        }
        self.articles = []
        self.base_url = "https://fedlex.data.admin.ch"
        
        # Load landesrecht and main section mappings
        self.landesrecht_sections = self._load_landesrecht_sections()
        self.main_sections = self._load_main_sections()
    
    def _load_landesrecht_sections(self):
        """Load landesrecht sections from JSON file"""
        try:
            with open('landesrecht_sections.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading landesrecht_sections.json: {e}")
            return {}
    
    def _load_main_sections(self):
        """Load main sections from JSON file"""
        try:
            with open('main_section.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading main_section.json: {e}")
            return {}
    
    def parse_xml_file(self, xml_file_path):
        """
        Parse a Swiss law XML file and extract articles
        
        Args:
            xml_file_path (str): Path to the XML file
            
        Returns:
            list: List of article objects with metadata
        """
        try:
            logger.info(f"Parsing XML file: {xml_file_path}")
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Debug: Print root element info
            logger.info(f"Root element: {root.tag}")
            logger.info(f"Root attributes: {root.attrib}")
            
            # Debug: Find all elements with 'article' in tag name
            all_elements = [elem.tag for elem in root.iter()]
            article_like = [tag for tag in all_elements if 'article' in tag.lower()]
            logger.info(f"Elements containing 'article': {article_like}")
            
            # Extract document metadata
            doc_metadata = self._extract_document_metadata(root)
            logger.info(f"Document metadata: {doc_metadata}")
            
            # Extract document home URL
            document_home_url = self._extract_document_home_url(root)
            if document_home_url:
                logger.info(f"Document home URL: {document_home_url}")
            else:
                logger.warning("Could not extract document home URL")
            
            # Extract all articles
            articles = self._extract_articles(root, doc_metadata, document_home_url)
            
            self.articles = articles
            logger.info(f"Successfully extracted {len(articles)} articles")
            return articles
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing XML file: {e}")
            return []
    
    def _extract_document_metadata(self, root):
        """Extract document-level metadata from the XML root"""
        metadata = {}
        
        # Extract document number (SR number) - try with and without namespace
        doc_number_elem = root.find('.//docNumber') or root.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}docNumber')
        if doc_number_elem is not None and doc_number_elem.text:
            metadata['doc_number'] = doc_number_elem.text.strip()
        
        # Extract document title - try with and without namespace
        doc_title_elem = root.find('.//docTitle') or root.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}docTitle')
        if doc_title_elem is not None:
            # Handle multi-line titles with <br/> tags
            # Convert the element to string and replace <br/> with spaces
            title_xml = ET.tostring(doc_title_elem, encoding='unicode')
            # Replace <br/> tags with spaces
            title_text = re.sub(r'<br\s*/?>', ' ', title_xml)
            # Remove all XML tags and get clean text
            title_text = re.sub(r'<[^>]+>', '', title_text)
            # Clean up extra whitespace
            title_text = re.sub(r'\s+', ' ', title_text).strip()
            metadata['doc_title'] = title_text
        
        # Extract FRBR information for hierarchical path
        frbr_work = root.find('.//FRBRWork') or root.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRWork')
        if frbr_work is not None:
            frbr_uri = frbr_work.find('FRBRuri') or frbr_work.find('{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRuri')
            if frbr_uri is not None:
                metadata['frbr_uri'] = frbr_uri.get('value', '')
        
        # Extract hierarchical path from document number
        doc_number = metadata.get('doc_number', '')
        if doc_number:
            metadata['hierarchical_path'] = self._extract_hierarchical_path(doc_number)
        
        # Extract dates
        dates = {}
        for date_elem in root.findall('.//FRBRdate') + root.findall('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRdate'):
            date_name = date_elem.get('name', '')
            date_value = date_elem.get('date', '')
            if date_name and date_value:
                dates[date_name] = date_value
        metadata['dates'] = dates
        
        return metadata
    
    def _extract_hierarchical_path(self, document_number):
        """Extract hierarchical storage path from document number"""
        if not document_number:
            return []
        
        path_parts = []
        
        # Extract first digit for landesrecht
        first_digit = document_number[0] if document_number else None
        if first_digit and first_digit in self.landesrecht_sections:
            path_parts.append(f"Landesrecht: {self.landesrecht_sections[first_digit]}")
        
        # Extract first two digits for main section
        if len(document_number) >= 2:
            first_two_digits = document_number[:2]
            # Find the matching section in the main_sections
            for section_key, sections in self.main_sections.items():
                for section in sections:
                    if section['number'] == first_two_digits:
                        path_parts.append(f"Main Section: {section['title']}")
                        break
                else:
                    continue
                break
        
        return path_parts
    
    def _extract_articles(self, root, doc_metadata, document_home_url=None):
        """Extract all articles from the XML document"""
        articles = []
        
        # Find all article elements - try different approaches
        article_elements = []
        
        # Method 1: Direct search without namespace
        article_elements = root.findall('.//article')
        
        # Method 2: Search with namespace if no articles found
        if not article_elements:
            article_elements = root.findall('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}article')
        
        # Method 3: Search in body element
        if not article_elements:
            body = root.find('.//body')
            if body is not None:
                article_elements = body.findall('.//article')
        
        logger.info(f"Found {len(article_elements)} article elements")
        
        for article_elem in article_elements:
            article_data = self._parse_article(article_elem, doc_metadata, document_home_url)
            if article_data:
                articles.append(article_data)
        
        return articles
    
    def _parse_article(self, article_elem, doc_metadata, document_home_url=None):
        """Parse individual article element"""
        # Create article_id with document number prefix
        original_eid = article_elem.get('eId', '')
        doc_number = doc_metadata.get('doc_number', '')
        article_id = f"{doc_number}_{original_eid}" if doc_number and original_eid else original_eid
        
        # Construct article URL if document home URL is provided
        article_url = None
        if document_home_url and original_eid:
            article_url = f"{document_home_url}#{original_eid}"
        
        article_data = {
            'article_id': article_id,
            'hierarchical_storage': doc_metadata.get('hierarchical_path', []),
            'document_number': doc_metadata.get('doc_number', ''),
            'document_title': doc_metadata.get('doc_title', ''),
            'article_number': '',
            'article_title': '',
            'article_text': '',
            'hyperlinks': [],
            'article_url': article_url,
            'document_home_url': document_home_url
        }
        
        # Extract article number - try with and without namespace
        num_elem = article_elem.find('.//num') or article_elem.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}num')
        if num_elem is not None:
            article_data['article_number'] = self._extract_text_content(num_elem)
        
        # Extract article title/heading - try with and without namespace
        heading_elem = article_elem.find('.//heading') or article_elem.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading')
        if heading_elem is not None:
            article_data['article_title'] = self._extract_text_content(heading_elem)
        
        # Extract article content and hyperlinks
        content_data = self._extract_article_content(article_elem)
        article_data['article_text'] = content_data['text']
        article_data['hyperlinks'] = content_data['hyperlinks']
        
        return article_data
    
    def _extract_article_content(self, article_elem):
        """Extract text content and hyperlinks from article"""
        text_parts = []
        hyperlinks = []
        
        # Find the heading element to start extraction after it
        heading_elem = article_elem.find('.//heading') or article_elem.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading')
        
        # Extract text content between heading and end of article
        article_text = self._extract_text_between_heading_and_article(article_elem, heading_elem)
        if article_text:
            text_parts.append(article_text)
        
        # Extract hyperlinks with ref_articles from the entire article
        hyperlinks = self._extract_hyperlinks_with_ref_articles(article_elem)
        
        # Deduplicate hyperlinks at article level
        unique_hyperlinks = []
        seen_urls = set()
        
        for link in hyperlinks:
            # Use URL as the deduplication key
            if link['url'] not in seen_urls:
                unique_hyperlinks.append(link)
                seen_urls.add(link['url'])
        
        return {
            'text': ' '.join(text_parts),
            'hyperlinks': unique_hyperlinks
        }
    
    def _extract_text_between_heading_and_article(self, article_elem, heading_elem):
        """Extract text content between heading and end of article, ignoring authorialNote content"""
        if not article_elem:
            return ""
        
        text_parts = []
        
        # Start collecting text after the heading element
        start_collecting = heading_elem is None  # If no heading, start immediately
        
        # Process only direct children of the article element
        for child in article_elem:
            # Check if we've reached the heading element
            if child == heading_elem:
                start_collecting = True
                continue
            
            # If we're collecting, extract text from this child
            if start_collecting:
                text_content = self._extract_text_without_authorial_notes(child)
                if text_content:
                    text_parts.append(text_content)
        
        # Join and clean up the text
        full_text = ' '.join(text_parts)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text
    
    def _is_authorial_note(self, elem):
        """Check if element is an authorialNote or contains authorialNote"""
        if elem is None:
            return False
        
        # Check if this element is an authorialNote
        if (elem.tag == 'authorialNote' or 
            elem.tag.endswith('}authorialNote')):
            return True
        
        # Check if any parent is an authorialNote
        current = elem
        while current is not None:
            if (current.tag == 'authorialNote' or 
                current.tag.endswith('}authorialNote')):
                return True
            current = current.getparent() if hasattr(current, 'getparent') else None
        
        return False
    
    def _extract_text_without_authorial_notes(self, elem):
        """Extract text content from element while skipping authorialNote content"""
        if elem is None:
            return ""
        
        text_parts = []
        
        # Get direct text content
        if elem.text and elem.text.strip():
            text_parts.append(elem.text.strip())
        
        # Process child elements
        for child in elem:
            # Skip authorialNote elements
            if not self._is_authorial_note(child):
                child_text = self._extract_text_without_authorial_notes(child)
                if child_text:
                    text_parts.append(child_text)
            
            # Get tail text (text after the element)
            if child.tail and child.tail.strip():
                text_parts.append(child.tail.strip())
        
        # Join and clean up
        result = ' '.join(text_parts)
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    def _extract_hyperlinks_with_ref_articles(self, article_elem):
        """Extract hyperlinks with ref_articles by collecting article references between authorialNotes"""
        hyperlinks = []
        
        # Get all text content from the article for pattern matching
        article_text = self._extract_text_without_authorial_notes(article_elem)
        
        # Find all authorialNote elements
        authorial_notes = []
        for elem in article_elem.iter():
            if self._is_authorial_note(elem):
                authorial_notes.append(elem)
        
        # Process each authorialNote and collect article references
        for i, authorial_note in enumerate(authorial_notes):
            # Extract hyperlinks from this authorialNote
            note_hyperlinks = self._extract_hyperlinks(authorial_note)
            
            # Collect article references for this authorialNote
            ref_articles = self._collect_ref_articles_for_authorial_note(
                article_elem, authorial_note, i, authorial_notes
            )
            
            # Add ref_articles to each hyperlink from this authorialNote
            for link in note_hyperlinks:
                link['ref_articles'] = ref_articles
                hyperlinks.append(link)
        
        return hyperlinks
    
    def _collect_ref_articles_for_authorial_note(self, article_elem, current_authorial_note, note_index, all_authorial_notes):
        """Collect article references between the end of previous authorialNote and current authorialNote"""
        ref_articles = []
        
        # Get the text content between authorialNotes
        text_between_notes = self._get_text_between_authorial_notes(
            article_elem, current_authorial_note, note_index, all_authorial_notes
        )
        
        # Find all "Artikel ##" patterns in the text
        import re
        artikel_pattern = r'Artikel\s+(\d+)'
        matches = re.findall(artikel_pattern, text_between_notes)
        
        # Convert to list of strings (article numbers) and deduplicate
        ref_articles = list(set(matches))
        
        return ref_articles
    
    def _get_text_between_authorial_notes(self, article_elem, current_authorial_note, note_index, all_authorial_notes):
        """Get text content between the end of previous authorialNote and current authorialNote"""
        text_parts = []
        
        # Find the start position (end of previous authorialNote or start of article)
        start_elem = None
        if note_index > 0:
            # Find the end of the previous authorialNote
            prev_authorial_note = all_authorial_notes[note_index - 1]
            start_elem = prev_authorial_note
        else:
            # Start from the beginning of the article
            start_elem = article_elem
        
        # Find the end position (start of current authorialNote)
        end_elem = current_authorial_note
        
        # Collect text between start and end elements
        collecting = False
        for elem in article_elem.iter():
            if elem == start_elem:
                collecting = True
                continue
            elif elem == end_elem:
                break
            
            if collecting and not self._is_authorial_note(elem):
                elem_text = self._extract_text_without_authorial_notes(elem)
                if elem_text:
                    text_parts.append(elem_text)
        
        return ' '.join(text_parts)
    
    def _extract_text_content(self, elem):
        """Extract clean text content from XML element"""
        if elem is None:
            return ""
        
        # Get all text content, handling nested elements
        text_parts = []
        
        # Get direct text content
        if elem.text and elem.text.strip():
            text_parts.append(elem.text.strip())
        
        # Get text from all child elements
        for child in elem.iter():
            if child != elem and child.text and child.text.strip():
                text_parts.append(child.text.strip())
        
        # Join and clean up the text
        full_text = ' '.join(text_parts)
        
        # Clean up extra whitespace
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text
    
    def _extract_hyperlinks(self, elem):
        """Extract hyperlinks and their associated text - only SR category URLs with eli/cc/ structure"""
        hyperlinks = []
        
        # Find all ref elements (hyperlinks in AkomaNtoso) - try with and without namespace
        ref_elements = elem.findall('.//ref') + elem.findall('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}ref')
        
        if len(ref_elements) != 0:
            print(ref_elements)
        for ref_elem in ref_elements:
            href = ref_elem.get('href', '')
            link_text = self._extract_text_content(ref_elem)
            
            if href and link_text:
                # Convert relative URLs to absolute
                if href.startswith('http'):
                    absolute_url = href
                else:
                    absolute_url = urljoin(self.base_url, href)
                
                # Only include URLs with eli/cc/ structure (SR category)
                if '/eli/cc/' in absolute_url:
                    hyperlinks.append({
                        'url': absolute_url,
                        'text': link_text,
                        'target_document': self._extract_target_document(href)
                    })
        
        return hyperlinks
    
    def _extract_target_document(self, href):
        """Extract target document information from hyperlink"""
        if not href:
            return ""
        
        # Extract SR number from href if present
        # Example: href="https://fedlex.data.admin.ch/eli/cc/2007/136"
        if 'eli/cc/' in href:
            parts = href.split('eli/cc/')[1].split('/')
            if len(parts) >= 2:
                return f"SR {parts[0]}.{parts[1]}"
        
        return ""
    
    def create_html_article(self, article_data):
        """Create HTML representation of an article"""
        html_parts = []
        
        # Article container
        html_parts.append(f'<div class="article" id="{article_data["article_id"]}">')
        
        # Hierarchical storage information
        if article_data['hierarchical_storage']:
            html_parts.append('<div class="hierarchical-storage">')
            html_parts.append('<h4>Storage Location:</h4>')
            html_parts.append('<ul>')
            for path_item in article_data['hierarchical_storage']:
                html_parts.append(f'<li>{path_item}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Document metadata
        html_parts.append('<div class="document-metadata">')
        html_parts.append(f'<h4>Document: {article_data["document_number"]}</h4>')
        html_parts.append(f'<h5>{article_data["document_title"]}</h5>')
        html_parts.append('</div>')
        
        # Article header
        html_parts.append('<div class="article-header">')
        html_parts.append(f'<h3>{article_data["article_number"]} {article_data["article_title"]}</h3>')
        html_parts.append('</div>')
        
        # Article content
        html_parts.append('<div class="article-content">')
        html_parts.append(f'<p>{article_data["article_text"]}</p>')
        html_parts.append('</div>')
        
        # Hyperlinks
        if article_data['hyperlinks']:
            html_parts.append('<div class="article-hyperlinks">')
            html_parts.append('<h4>Related References:</h4>')
            html_parts.append('<ul>')
            for link in article_data['hyperlinks']:
                html_parts.append(f'<li><a href="{link["url"]}" target="_blank">{link["text"]}</a>')
                if link['target_document']:
                    html_parts.append(f' <span class="target-doc">({link["target_document"]})</span>')
                html_parts.append('</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def save_articles_to_html(self, output_file="swiss_law_articles.html"):
        """Save all articles as HTML file"""
        try:
            html_content = []
            html_content.append('<!DOCTYPE html>')
            html_content.append('<html lang="de">')
            html_content.append('<head>')
            html_content.append('<meta charset="UTF-8">')
            html_content.append('<title>Swiss Law Articles</title>')
            html_content.append('<style>')
            html_content.append('''
                body { font-family: Arial, sans-serif; margin: 20px; }
                .article { border: 1px solid #ccc; margin: 20px 0; padding: 15px; }
                .hierarchical-storage { background-color: #f0f0f0; padding: 10px; margin: 10px 0; }
                .document-metadata { background-color: #e8f4f8; padding: 10px; margin: 10px 0; }
                .article-header { border-bottom: 2px solid #333; padding-bottom: 10px; }
                .article-content { margin: 15px 0; }
                .article-hyperlinks { background-color: #f9f9f9; padding: 10px; margin: 10px 0; }
                .target-doc { color: #666; font-style: italic; }
                h3 { color: #2c3e50; }
                h4 { color: #34495e; }
                h5 { color: #7f8c8d; }
            ''')
            html_content.append('</style>')
            html_content.append('</head>')
            html_content.append('<body>')
            html_content.append('<h1>Swiss Law Articles</h1>')
            
            for article in self.articles:
                html_content.append(self.create_html_article(article))
            
            html_content.append('</body>')
            html_content.append('</html>')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html_content))
            
            logger.info(f"Articles saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving articles to HTML: {e}")
    
    def save_articles_to_json(self, output_file="swiss_law_articles.json"):
        """Save all articles as JSON file for LLM processing"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Articles saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving articles to JSON: {e}")
    
    def extract_urls(self, xml_file_path):
        """
        Extract canonical URLs for document and articles from XML file

        CURRENTLY HARDCODED. THE INFO IS NOT PULLED DIRECTLY FROM THE XML FILE.
        
        Args:
            xml_file_path (str): Path to the XML file
            
        Returns:
            dict: Dictionary containing document home URL and article URLs
        """
        try:
            logger.info(f"Extracting URLs from XML file: {xml_file_path}")
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Extract document home URL
            document_home_url = self._extract_document_home_url(root)
            if not document_home_url:
                logger.warning("Could not extract document home URL - FRBR Expression URI may be malformed or missing")
                return None
            
            # Extract article URLs
            article_urls = self._extract_article_urls(root, document_home_url)
            
            url_data = {
                'document_home_url': document_home_url,
                'articles': article_urls
            }
            
            logger.info(f"Successfully extracted URLs: {len(article_urls)} articles")
            return url_data
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error during URL extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting URLs from XML file: {e}")
            return None
    
    def _extract_document_home_url(self, root):
        """Extract the canonical document home URL from FRBR Expression URI"""
        try:
            # Find FRBR Expression URI - try with and without namespace
            frbr_expression = root.find('.//FRBRExpression') or root.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRExpression')
            if frbr_expression is None:
                logger.warning("FRBR Expression element not found")
                return None
            
            frbr_uri_elem = frbr_expression.find('FRBRuri') or frbr_expression.find('{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRuri')
            if frbr_uri_elem is None:
                logger.warning("FRBR URI element not found")
                return None
            
            frbr_uri = frbr_uri_elem.get('value', '')
            if not frbr_uri:
                logger.warning("FRBR URI value is empty")
                return None
            
            logger.info(f"Found FRBR Expression URI: {frbr_uri}")
            
            # Parse the URI to extract components
            # Example: https://fedlex.data.admin.ch/eli/cc/2016/350/20160701/de
            if '/eli/cc/' not in frbr_uri:
                logger.warning(f"FRBR URI does not contain expected /eli/cc/ pattern: {frbr_uri}")
                return None
            
            # Extract path components after /eli/cc/
            path_part = frbr_uri.split('/eli/cc/')[1]
            path_components = path_part.split('/')
            
            if len(path_components) < 4:
                logger.warning(f"FRBR URI has insufficient path components: {path_components}")
                return None
            
            # Extract year, number, and language
            year = path_components[0]  # 2016
            number = path_components[1]  # 350
            language = path_components[3]  # de
            
            # Construct the canonical document home URL
            document_home_url = f"https://www.fedlex.admin.ch/eli/cc/{year}/{number}/{language}"
            
            # Validate the constructed URL
            if self._validate_document_url(document_home_url):
                logger.info(f"Constructed document home URL: {document_home_url}")
                return document_home_url
            else:
                logger.warning(f"Constructed document home URL failed validation: {document_home_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting document home URL: {e}")
            return None
    
    def _extract_article_urls(self, root, document_home_url):
        """Extract article-specific URLs"""
        article_urls = []
        
        try:
            # Find all article elements - try different approaches
            article_elements = []
            
            # Method 1: Direct search without namespace
            article_elements = root.findall('.//article')
            
            # Method 2: Search with namespace if no articles found
            if not article_elements:
                article_elements = root.findall('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}article')
            
            # Method 3: Search in body element
            if not article_elements:
                body = root.find('.//body')
                if body is not None:
                    article_elements = body.findall('.//article')
            
            logger.info(f"Found {len(article_elements)} article elements for URL extraction")
            
            for article_elem in article_elements:
                article_id = article_elem.get('eId', '')
                if not article_id:
                    logger.warning("Article element missing eId attribute")
                    continue
                
                # Construct article-specific URL
                article_url = f"{document_home_url}#{article_id}"
                
                # Validate the article URL
                if self._validate_article_url(article_url):
                    article_urls.append({
                        'article_id': article_id,
                        'article_url': article_url
                    })
                    logger.info(f"Constructed article URL: {article_url}")
                else:
                    logger.warning(f"Article URL failed validation: {article_url}")
            
            return article_urls
            
        except Exception as e:
            logger.error(f"Error extracting article URLs: {e}")
            return []
    
    def _validate_document_url(self, url):
        """Validate document home URL format"""
        import re
        # Pattern: https://www.fedlex.admin.ch/eli/cc/YYYY/NNNN/LL
        pattern = r'^https://www\.fedlex\.admin\.ch/eli/cc/\d{4}/\d+/[a-z]{2}$'
        return bool(re.match(pattern, url))
    
    def _validate_article_url(self, url):
        """Validate article-specific URL format"""
        import re
        # Pattern: https://www.fedlex.admin.ch/eli/cc/YYYY/NNNN/LL#art_N
        pattern = r'^https://www\.fedlex\.admin\.ch/eli/cc/\d{4}/\d+/[a-z]{2}#art_\d+$'
        return bool(re.match(pattern, url))
    
    def print_urls_summary(self, url_data):
        """Print summary of extracted URLs"""
        if not url_data:
            print("No URL data available.")
            return
        
        print(f"\n{'='*60}")
        print("SWISS LAW URLS SUMMARY")
        print(f"{'='*60}")
        
        print(f"\nDocument Home URL:")
        print(f"  {url_data['document_home_url']}")
        
        print(f"\nArticle URLs ({len(url_data['articles'])} articles):")
        for i, article in enumerate(url_data['articles'], 1):
            print(f"  {i}. {article['article_id']}: {article['article_url']}")
        
        print(f"\n{'='*60}")
        print(f"Total article URLs extracted: {len(url_data['articles'])}")

    def print_articles_summary(self):
        """Print summary of extracted articles"""
        if not self.articles:
            print("No articles found.")
            return
        
        print(f"\n{'='*60}")
        print("SWISS LAW ARTICLES SUMMARY")
        print(f"{'='*60}")
        
        for i, article in enumerate(self.articles, 1):
            print(f"\nArticle {i}:")
            print(f"  ID: {article['article_id']}")
            print(f"  Number: {article['article_number']}")
            print(f"  Title: {article['article_title']}")
            print(f"  Document: {article['document_number']} - {article['document_title']}")
            print(f"  Article URL: {article.get('article_url', 'N/A')}")
            print(f"  Document Home URL: {article.get('document_home_url', 'N/A')}")
            print(f"  Hyperlinks: {len(article['hyperlinks'])}")
            print(f"  Text length: {len(article['article_text'])} characters")
        
        print(f"\n{'='*60}")
        print(f"Total articles extracted: {len(self.articles)}")

def main():
    """Main function to run the XML scraper"""
    scraper = SwissLawXMLScraper()
    
    # Parse the SR-901.022.2 XML file
    xml_file = "SR-901.022.2-01072016-DE.xml"
    
    if not os.path.exists(xml_file):
        logger.error(f"XML file not found: {xml_file}")
        return
    
    # Parse the XML file for articles (now includes URLs)
    articles = scraper.parse_xml_file(xml_file)
    
    if articles:
        # Print articles summary (now includes URLs)
        scraper.print_articles_summary()
        
        # Save to HTML and JSON (now includes URLs)
        scraper.save_articles_to_html()
        scraper.save_articles_to_json()
        
        logger.info("XML scraping with URLs completed successfully!")
    else:
        logger.warning("No articles were extracted from the XML file.")

if __name__ == "__main__":
    main()
