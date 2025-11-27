#!/usr/bin/env python3
"""
GPT Large LLM Input Generator for Swiss Law Documents
Extracts legal cross-references from AkomaNtoso XML format for ref-resolver
"""

import xml.etree.ElementTree as ET
import json
import re
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalRefExtractor:
    """Extracts legal cross-references from Swiss law XML documents"""
    
    def __init__(self):
        self.namespaces = {
            'akn': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0',
            'fedlex': 'http://fedlex.admin.ch/'
        }
    
    def extract_text_content(self, elem, include_authorial_notes=True, current_authorial_note=None):
        """
        Extract all text content from an element and its children
        
        Args:
            elem: The element to extract text from
            include_authorial_notes: Whether to include authorialNote content
            current_authorial_note: If provided, only include THIS authorialNote, exclude others
        """
        if elem is None:
            return ""
        
        text_parts = []
        
        # Add element's direct text
        if elem.text:
            text_parts.append(elem.text)
        
        # Recursively process children
        for child in elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            # Handle authorialNote elements
            if child_tag == 'authorialNote':
                if current_authorial_note is not None:
                    # Only include the CURRENT authorialNote, exclude all others
                    if child == current_authorial_note:
                        # Include this authorialNote's content
                        text_parts.append(self.extract_text_content(child, True, current_authorial_note))
                    # Skip other authorialNotes but keep their tail text
                    if child.tail:
                        text_parts.append(child.tail)
                    continue
                elif not include_authorial_notes:
                    # Skip all authorialNotes but keep tail text
                    if child.tail:
                        text_parts.append(child.tail)
                    continue
            
            # Process child recursively
            text_parts.append(self.extract_text_content(child, include_authorial_notes, current_authorial_note))
            if child.tail:
                text_parts.append(child.tail)
        
        return ''.join(text_parts)
    
    def get_paragraph_text(self, authorial_note_elem, parent_map):
        """
        Get the full paragraph text that contains the authorialNote.
        Includes ONLY the current authorialNote, excludes other authorialNotes in the same paragraph.
        """
        # Find the parent paragraph-like element using parent_map
        current = authorial_note_elem
        paragraph = None
        
        # Traverse up the tree to find a paragraph-like element
        for _ in range(15):  # Limit depth search
            if current is None:
                break
            
            parent = parent_map.get(current)
            
            if parent is not None:
                # Check if parent is a paragraph element
                tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                
                # Look for p, content, paragraph, or other text-containing elements
                if tag in ['p', 'content', 'paragraph', 'listIntroduction', 'item']:
                    paragraph = parent
                    # If we found a 'p', check if there's a 'content' parent above it
                    if tag == 'p':
                        content_parent = parent_map.get(parent)
                        if content_parent is not None:
                            content_tag = content_parent.tag.split('}')[-1] if '}' in content_parent.tag else content_parent.tag
                            if content_tag == 'content':
                                # Use the content element for full context
                                paragraph = content_parent
                    break
            
            current = parent
        
        if paragraph is not None:
            # Extract full text, including ONLY the current authorialNote, excluding others
            full_text = self.extract_text_content(
                paragraph, 
                include_authorial_notes=True, 
                current_authorial_note=authorial_note_elem
            ).strip()
            # Normalize whitespace
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            return full_text
        
        # Fallback: try to get some context from just this authorialNote
        fallback_text = self.extract_text_content(
            authorial_note_elem, 
            include_authorial_notes=True
        ).strip()
        return re.sub(r'\s+', ' ', fallback_text).strip()
    
    def extract_acronyms_from_preamble(self, preamble_elem):
        """
        Extract acronyms in parentheses from preamble text and associate with nearest SR links.
        
        Strategy:
        1. Find all single-word acronyms in parentheses in preamble (excluding those inside authorialNotes)
        2. Find all authorialNotes with SR links
        3. For each acronym, find the nearest authorialNote and associate them
        
        Returns a list of dicts: [{acronym, sr_link, url}, ...]
        """
        acronym_data = []
        
        # Step 1: Collect all authorialNotes with their SR links and positions
        authorial_notes_with_links = []
        all_elements = list(preamble_elem.iter())
        
        for authorial_note in preamble_elem.iter():
            tag = authorial_note.tag.split('}')[-1] if '}' in authorial_note.tag else authorial_note.tag
            if tag != 'authorialNote':
                continue
            
            # Find SR link in this authorialNote
            sr_link = None
            url = None
            for ref_elem in authorial_note.iter():
                ref_tag = ref_elem.tag.split('}')[-1] if '}' in ref_elem.tag else ref_elem.tag
                if ref_tag == 'ref':
                    href = ref_elem.get('href', '')
                    
                    # Try multiple ways to get fedlex:rs-uri attribute
                    rs_uri = ''
                    rs_uri = ref_elem.get('{http://fedlex.admin.ch/}rs-uri', '')
                    if not rs_uri:
                        rs_uri = ref_elem.get('fedlex:rs-uri', '')
                    if not rs_uri:
                        for attr_name, attr_value in ref_elem.attrib.items():
                            if 'rs-uri' in attr_name:
                                rs_uri = attr_value
                                break
                    
                    # Check both href and rs-uri for eli/cc/ pattern
                    found_url = None
                    if '/eli/cc/' in href:
                        found_url = href
                    elif '/eli/cc/' in rs_uri:
                        found_url = rs_uri
                    
                    if found_url:
                        link_text = self.extract_text_content(ref_elem, include_authorial_notes=True).strip()
                        sr_link = link_text
                        url = found_url
                        break
            
            if sr_link and url:
                try:
                    position = all_elements.index(authorial_note)
                    authorial_notes_with_links.append({
                        'element': authorial_note,
                        'position': position,
                        'sr_link': sr_link,
                        'url': url
                    })
                except ValueError:
                    pass
        
        if not authorial_notes_with_links:
            return acronym_data
        
        # Step 2: Find all acronyms (single words in parentheses) NOT inside authorialNotes
        acronym_pattern = r'\(([A-Za-zäöüÄÖÜß]+)\)'
        acronyms_found = []  # List of (acronym, element, position)
        
        for elem in preamble_elem.iter():
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            # Check element's text (but skip if this element IS an authorialNote or is inside one)
            if elem.text:
                # Check if this element or any parent is an authorialNote
                is_inside_authorial_note = False
                current = elem
                for _ in range(20):  # Check up to 20 levels up
                    if current is None:
                        break
                    current_tag = current.tag.split('}')[-1] if '}' in current.tag else current.tag
                    if current_tag == 'authorialNote':
                        is_inside_authorial_note = True
                        break
                    # Move up (need to find parent)
                    parent = None
                    for p in preamble_elem.iter():
                        if current in list(p):
                            parent = p
                            break
                    current = parent
                
                if not is_inside_authorial_note:
                    matches = re.finditer(acronym_pattern, elem.text)
                    for match in matches:
                        acronym = match.group(1)
                        try:
                            position = all_elements.index(elem)
                            acronyms_found.append((acronym, elem, position))
                        except ValueError:
                            pass
            
            # Check element's tail (text after the element's closing tag)
            # The tail is NOT inside the element, so even if elem is an authorialNote,
            # its tail is outside of it
            if elem.tail:
                matches = re.finditer(acronym_pattern, elem.tail)
                for match in matches:
                    acronym = match.group(1)
                    try:
                        position = all_elements.index(elem)
                        acronyms_found.append((acronym, elem, position))
                    except ValueError:
                        pass
        
        # Step 3: For each acronym, find the nearest authorialNote
        seen_acronyms = set()
        for acronym, elem, acronym_pos in acronyms_found:
            # Skip duplicates
            if acronym in seen_acronyms:
                continue
            
            # Find nearest authorialNote
            nearest = min(authorial_notes_with_links, 
                         key=lambda x: abs(x['position'] - acronym_pos))
            
            acronym_data.append({
                'acronym': acronym,
                'sr_link': nearest['sr_link'],
                'url': nearest['url']
            })
            seen_acronyms.add(acronym)
        
        return acronym_data
    
    def find_acronym_before_authorial_note(self, authorial_note_elem, parent_map):
        """
        Find all-caps acronym immediately before the authorialNote.
        Looks for patterns like: "ACRONYM <authorialNote>" or "(ACRONYM) <authorialNote>"
        """
        # Get the parent element
        parent = parent_map.get(authorial_note_elem)
        if parent is None:
            return None
        
        # Get all children of the parent
        children = list(parent)
        
        # Find the index of the current authorialNote
        try:
            note_index = children.index(authorial_note_elem)
        except ValueError:
            return None
        
        # Look at text immediately before this authorialNote
        # Check the tail of the previous sibling or the parent's text
        text_before = ""
        
        if note_index > 0:
            # Get the tail of the previous sibling
            prev_sibling = children[note_index - 1]
            if prev_sibling.tail:
                text_before = prev_sibling.tail
        else:
            # Get the parent's direct text
            if parent.text:
                text_before = parent.text
        
        # Pattern to match all-caps acronyms (with or without parentheses) at the end
        # Matches: "text ACRONYM " or "text (ACRONYM) "
        acronym_pattern = r'(?:\(([A-Z]{2,})\)|([A-Z]{2,}))\s*$'
        match = re.search(acronym_pattern, text_before)
        
        if match:
            # Return the acronym (could be in group 1 or 2)
            return match.group(1) if match.group(1) else match.group(2)
        
        return None
    
    def find_lines_with_acronym(self, article_elem, acronym, parent_map):
        """
        Find lines in the article containing the acronym (not inside authorialNote).
        Only searches within <content> elements to avoid capturing article titles.
        
        Returns a list of unique lines.
        """
        lines = []
        
        # First, find all <content> elements in the article
        content_elements = []
        for elem in article_elem.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'content':
                content_elements.append(elem)
        
        # Now search within each <content> element
        for content_elem in content_elements:
            # Get leaf-level elements within this content
            for elem in content_elem.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                # Only process specific leaf-level elements
                if tag not in ['p', 'item', 'listIntroduction', 'subheading']:
                    continue
                
                # Skip authorialNote elements
                if tag == 'authorialNote':
                    continue
                
                # Check if element is inside an authorialNote
                is_inside_authorial_note = False
                current = elem
                for _ in range(20):
                    if current is None:
                        break
                    current_tag = current.tag.split('}')[-1] if '}' in current.tag else current.tag
                    if current_tag == 'authorialNote':
                        is_inside_authorial_note = True
                        break
                    parent = None
                    for p in content_elem.iter():
                        if current in list(p):
                            parent = p
                            break
                    current = parent
                
                if is_inside_authorial_note:
                    continue
                
                # Extract text excluding ALL authorialNotes
                text = self.extract_text_content(elem, include_authorial_notes=False)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if not text:
                    continue
                
                # Check if this line contains the acronym
                if acronym and acronym in text:
                    lines.append(text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return unique_lines
    
    def find_artikel_references(self, article_elem, existing_snippets=None):
        """
        Find all lines in the article containing "Art. ##", "Artikel ##", or "Artikeln ##"
        (not inside authorialNote). Only searches within <content> elements
        to avoid capturing article titles.
        
        Args:
            article_elem: The article element to search
            existing_snippets: Set of snippets from OTHER item types (to avoid overlap with preamble/SR links)
                              Does NOT prevent same snippet from appearing in different articles
        
        Returns a list of unique lines containing Artikel references.
        """
        if existing_snippets is None:
            existing_snippets = set()
        
        lines = []
        artikel_pattern = r'\b(?:Art\.|Artikel|Artikeln)\s+\d+[a-z]*\b'
        
        # First, find all <content> elements in the article
        content_elements = []
        for elem in article_elem.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'content':
                content_elements.append(elem)
        
        # Now search within each <content> element
        for content_elem in content_elements:
            # Get leaf-level elements within this content
            for elem in content_elem.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                # Only process specific leaf-level elements
                if tag not in ['p', 'item', 'listIntroduction', 'subheading']:
                    continue
                
                # Skip authorialNote elements
                if tag == 'authorialNote':
                    continue
                
                # Check if element is inside an authorialNote
                is_inside_authorial_note = False
                current = elem
                for _ in range(20):
                    if current is None:
                        break
                    current_tag = current.tag.split('}')[-1] if '}' in current.tag else current.tag
                    if current_tag == 'authorialNote':
                        is_inside_authorial_note = True
                        break
                    parent = None
                    for p in content_elem.iter():
                        if current in list(p):
                            parent = p
                            break
                    current = parent
                
                if is_inside_authorial_note:
                    continue
                
                # Extract text excluding ALL authorialNotes
                text = self.extract_text_content(elem, include_authorial_notes=False)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if not text:
                    continue
                
                # Check if this line contains Art. ## or Artikel ##
                if re.search(artikel_pattern, text):
                    # Always add - we'll check for duplicates later in the calling code
                    lines.append(text)
        
        # Remove hierarchical duplicates (if one line is substring of another, keep only the longer one)
        # and remove exact duplicates
        filtered_lines = []
        for i, line in enumerate(lines):
            is_substring = False
            for j, other_line in enumerate(lines):
                if i != j and line in other_line and line != other_line:
                    # This line is a substring of another line
                    is_substring = True
                    break
            if not is_substring:
                filtered_lines.append(line)
        
        # Remove exact duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in filtered_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return unique_lines
    
    def find_preamble_acronym_references(self, root, preamble_acronym_data, parent_map):
        """
        Find all references to preamble acronyms in articles and create JSON items.
        
        Args:
            root: XML root element
            preamble_acronym_data: List of {acronym, sr_link, url} from preamble
            parent_map: Parent mapping for traversal
            
        Returns:
            List of JSON items for preamble acronym references
        """
        items = []
        
        if not preamble_acronym_data:
            return items
        
        # Find all articles
        for article in root.iter():
            tag = article.tag.split('}')[-1] if '}' in article.tag else article.tag
            if tag != 'article':
                continue
            
            article_eid = article.get('eId')
            if not article_eid:
                continue
            
            # For each preamble acronym, check if it's referenced in this article
            for acronym_info in preamble_acronym_data:
                acronym = acronym_info['acronym']
                sr_link = acronym_info['sr_link']
                url = acronym_info['url']
                
                # Search all text in the article (excluding authorialNotes)
                # Collect ALL occurrences and their contexts
                found_elements = []
                
                for elem in article.iter():
                    elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    
                    # Skip authorialNote elements themselves
                    if elem_tag == 'authorialNote':
                        continue
                    
                    # Check if this element is inside an authorialNote
                    is_inside_authorial_note = False
                    current = elem
                    for _ in range(20):
                        if current is None:
                            break
                        current_tag = current.tag.split('}')[-1] if '}' in current.tag else current.tag
                        if current_tag == 'authorialNote':
                            is_inside_authorial_note = True
                            break
                        # Find parent
                        parent = None
                        for p in article.iter():
                            if current in list(p):
                                parent = p
                                break
                        current = parent
                    
                    if is_inside_authorial_note:
                        continue
                    
                    # Check element's text
                    if elem.text and acronym in elem.text:
                        found_elements.append(elem)
                        # Don't break - keep looking for more occurrences
                    
                    # Check element's tail (text after closing tag)
                    elif elem.tail and acronym in elem.tail:
                        found_elements.append(elem)
                        # Don't break - keep looking for more occurrences
                
                # If acronym was found, create ONE JSON item with all contexts
                if found_elements:
                    # Collect all snippet contexts
                    snippet_parts = []
                    seen_snippets = set()  # To avoid duplicates
                    
                    for found_element in found_elements:
                        # Get the enclosing paragraph-like element for snippet
                        snippet_element = found_element
                        
                        # Try to find a parent paragraph-like element for better context
                        current = found_element
                        for _ in range(10):
                            if current is None:
                                break
                            tag = current.tag.split('}')[-1] if '}' in current.tag else current.tag
                            if tag in ['p', 'content', 'paragraph', 'heading', 'listIntroduction', 'item', 'num', 'subheading']:
                                snippet_element = current
                                break
                            # Find parent
                            parent = None
                            for p in article.iter():
                                if current in list(p):
                                    parent = p
                                    break
                            current = parent
                        
                        # Get the full text (excluding authorialNotes)
                        snippet_text = self.extract_text_content(snippet_element, include_authorial_notes=False)
                        snippet_text = re.sub(r'\s+', ' ', snippet_text).strip()
                        
                        # Only add if not already seen (avoid duplicates)
                        if snippet_text and snippet_text not in seen_snippets:
                            snippet_parts.append(snippet_text)
                            seen_snippets.add(snippet_text)
                    
                    # Combine all snippets with separator
                    combined_snippet = ' ... '.join(snippet_parts)
                    
                    item = {
                        'ARTICLE_EID': article_eid,
                        'TARGET_SR': sr_link,
                        'TARGET_URL': url,
                        'SNIPPET': combined_snippet,
                        'INSIDE_AUTHORIALNOTE': sr_link,  # Per requirement: same as TARGET_SR
                        'preamble_acronym_name': acronym,  # Add the acronym name
                        'item_type': 'preamble_acronym'
                    }
                    
                    items.append(item)
        
        return items
    
    def find_enclosing_context(self, elem, parent_map):
        """Find if element is within an article or preamble using parent map"""
        current = elem
        
        for _ in range(20):  # Limit depth search
            if current is None:
                break
            
            parent = parent_map.get(current)
            
            if parent is not None:
                parent_tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                
                if parent_tag == 'article':
                    article_eid = parent.get('eId')
                    return ('article', article_eid)
                elif parent_tag == 'preamble':
                    return ('preamble', 'preamble')
            
            current = parent
        
        return (None, None)
    
    def process_xml_file(self, xml_file_path):
        """Process XML file and extract legal cross-references"""
        try:
            logger.info(f"Processing XML file: {xml_file_path}")
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Build parent map for traversal
            parent_map = {c: p for p in root.iter() for c in p}
            logger.info(f"Built parent map with {len(parent_map)} elements")
            
            results = []
            
            # First, find preamble and extract acronyms with their SR links
            preamble = root.find('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}preamble')
            if preamble is None:
                preamble = root.find('.//preamble')
            
            preamble_acronym_data = []
            if preamble is not None:
                preamble_acronym_data = self.extract_acronyms_from_preamble(preamble)
                if preamble_acronym_data:
                    # Create callback with acronym names and their SR links
                    acronym_items = [
                        {
                            'acronym': item['acronym'],
                            'sr_link': item['sr_link'],
                            'url': item['url']
                        } 
                        for item in preamble_acronym_data
                    ]
                    callback_item = {
                        'item_type': 'preamble_callback',
                        'acronyms': acronym_items,
                        'description': 'Preamble acronyms for reference detection'
                    }
                    results.append(callback_item)
                    acronym_names = [item['acronym'] for item in preamble_acronym_data]
                    logger.info(f"Found {len(preamble_acronym_data)} preamble acronyms: {acronym_names}")
            
            # Process all authorialNote elements
            item_number = 1
            authorial_notes_count = 0
            for authorial_note in root.iter():
                # Check if this is an authorialNote element
                tag = authorial_note.tag.split('}')[-1] if '}' in authorial_note.tag else authorial_note.tag
                if tag != 'authorialNote':
                    continue
                
                authorial_notes_count += 1
                logger.debug(f"Processing authorialNote #{authorial_notes_count}")
                
                # Find the enclosing article or preamble
                context_type, article_eid = self.find_enclosing_context(authorial_note, parent_map)
                
                logger.debug(f"  Context: {context_type}, Article EID: {article_eid}")
                
                # Skip if not in article or preamble
                if context_type is None:
                    logger.debug(f"  Skipping - not in article or preamble")
                    continue
                
                # Get the full inner text of authorialNote
                inside_authorialnote = self.extract_text_content(authorial_note, include_authorial_notes=True).strip()
                
                # Find all hyperlinks with eli/cc in this authorialNote
                # Try both with and without namespace
                ref_elements = []
                ref_elements.extend(authorial_note.findall('.//ref'))
                ref_elements.extend(authorial_note.findall('.//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}ref'))
                
                # Also try direct iteration
                for elem in authorial_note.iter():
                    elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if elem_tag == 'ref' and elem not in ref_elements:
                        ref_elements.append(elem)
                
                logger.debug(f"Found {len(ref_elements)} ref elements in authorialNote within {article_eid}")
                
                for ref_elem in ref_elements:
                    href = ref_elem.get('href', '')
                    
                    # Try multiple ways to get fedlex:rs-uri attribute
                    rs_uri = ''
                    # Method 1: With namespace
                    rs_uri = ref_elem.get('{http://fedlex.admin.ch/}rs-uri', '')
                    # Method 2: Without namespace (fallback)
                    if not rs_uri:
                        rs_uri = ref_elem.get('fedlex:rs-uri', '')
                    # Method 3: Iterate through attrib dict
                    if not rs_uri:
                        for attr_name, attr_value in ref_elem.attrib.items():
                            if 'rs-uri' in attr_name:
                                rs_uri = attr_value
                                break
                    
                    logger.debug(f"  Checking href: {href}, rs-uri: {rs_uri}")
                    
                    # Collect URLs that contain eli/cc/ pattern
                    urls_to_process = []
                    if '/eli/cc/' in href:
                        urls_to_process.append(href)
                    if '/eli/cc/' in rs_uri:
                        urls_to_process.append(rs_uri)
                    
                    # Process each URL found (duplicate filter will handle if they're the same)
                    for url in urls_to_process:
                        # Extract SR number from the link text
                        link_text = self.extract_text_content(ref_elem, include_authorial_notes=True).strip()
                        
                        # Get the full paragraph text
                        snippet = self.get_paragraph_text(authorial_note, parent_map)
                        
                        # Normalize whitespace in authorialNote content
                        inside_authorialnote_normalized = re.sub(r'\s+', ' ', inside_authorialnote).strip()
                        
                        item = {
                            'ITEM': item_number,
                            'ARTICLE_EID': article_eid,
                            'TARGET_SR': link_text,
                            'TARGET_URL': url,  # Use the current URL being processed
                            'SNIPPET': snippet,
                            'INSIDE_AUTHORIALNOTE': inside_authorialnote_normalized
                        }
                        
                        # Check for acronym before authorialNote (only for articles, not preamble)
                        has_local_acronym = False
                        if context_type == 'article':
                            acronym = self.find_acronym_before_authorial_note(authorial_note, parent_map)
                            if acronym:
                                item['acronym'] = acronym
                                has_local_acronym = True
                                logger.debug(f"  Found acronym: {acronym}")
                                
                                # Find the article element
                                article_elem = None
                                current = authorial_note
                                for _ in range(20):
                                    parent = parent_map.get(current)
                                    if parent is not None:
                                        parent_tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                                        if parent_tag == 'article':
                                            article_elem = parent
                                            break
                                    current = parent
                                
                                # Find lines with acronym references only
                                if article_elem is not None:
                                    snippet_acronym_lines = self.find_lines_with_acronym(
                                        article_elem, acronym, parent_map
                                    )
                                    if snippet_acronym_lines:
                                        item['snippet_acronym'] = snippet_acronym_lines
                                        logger.debug(f"  Found {len(snippet_acronym_lines)} lines with acronym")
                        
                        # Set item_type based on whether it has a local acronym
                        if has_local_acronym:
                            item['item_type'] = 'SR_link_with_local_acronym'
                        else:
                            item['item_type'] = 'SR_link_detection'
                        
                        results.append(item)
                        logger.info(f"Item {item_number}: {article_eid} -> {link_text} (from {url})")
                        item_number += 1
            
            logger.info(f"Total authorialNotes found: {authorial_notes_count}")
            
            # Now find preamble acronym references in articles
            preamble_ref_items = self.find_preamble_acronym_references(root, preamble_acronym_data, parent_map)
            
            # Add ITEM numbers to preamble reference items
            for preamble_item in preamble_ref_items:
                preamble_item['ITEM'] = item_number
                results.append(preamble_item)
                logger.info(f"Item {item_number}: {preamble_item['ARTICLE_EID']} -> {preamble_item['TARGET_SR']} (preamble acronym ref)")
                item_number += 1
            
            # Collect all existing snippets to avoid duplication with OTHER item types
            # Track as (article_eid, snippet) pairs for artikel_reference deduplication
            existing_snippets_from_other_types = set()  # Snippets from preamble_acronym, SR_link, etc.
            existing_artikel_pairs = set()  # Track (article_eid, snippet) pairs for artikel_reference items
            
            for item in results:
                article_eid = item.get('ARTICLE_EID')
                if 'SNIPPET' in item:
                    existing_snippets_from_other_types.add(item['SNIPPET'])
                if 'snippet_acronym' in item:
                    for line in item['snippet_acronym']:
                        existing_snippets_from_other_types.add(line)
            
            # Now find Artikel references in ALL articles
            logger.info("Searching for Artikel references in all articles...")
            for article in root.iter():
                tag = article.tag.split('}')[-1] if '}' in article.tag else article.tag
                if tag != 'article':
                    continue
                
                article_eid = article.get('eId')
                if not article_eid:
                    continue
                
                # Find Artikel references in this article (not used to filter, just for documentation)
                artikel_lines = self.find_artikel_references(article, None)
                
                # Create an item for each unique line with Artikel reference
                for line in artikel_lines:
                    # Skip if this snippet already exists in OTHER item types (preamble_acronym, SR_link, etc.)
                    if line in existing_snippets_from_other_types:
                        continue
                    
                    # Skip if this (article_eid, snippet) pair already exists in artikel_reference items
                    if (article_eid, line) in existing_artikel_pairs:
                        continue
                    
                    # Create new artikel_reference item
                    item = {
                        'ITEM': item_number,
                        'ARTICLE_EID': article_eid,
                        'SNIPPET': line,
                        'item_type': 'artikel_reference'
                    }
                    results.append(item)
                    existing_artikel_pairs.add((article_eid, line))  # Mark pair as used
                    logger.info(f"Item {item_number}: {article_eid} (artikel ref)")
                    item_number += 1
            
            logger.info(f"Total items extracted: {len(results)}")
            return results
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing XML file: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_to_json(self, data, output_file):
        """Save extracted data to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False

def main():
    """Main function"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 GPT_LLM_input_generator.py <XML_FILE>")
        print("Example: python3 GPT_LLM_input_generator.py SR-611.01-01012026-DE.xml")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    # Generate output filename based on input filename
    base_name = os.path.basename(xml_file)  # Remove path if present
    name_without_ext = os.path.splitext(base_name)[0]  # Remove .xml extension
    output_file = f"GPT_Large_LLM_input_{name_without_ext}.json"
    
    # Create extractor
    extractor = LegalRefExtractor()
    
    # Process XML file
    results = extractor.process_xml_file(xml_file)
    
    if results:
        # Save to JSON
        if extractor.save_to_json(results, output_file):
            logger.info(f"Successfully processed {xml_file}")
            logger.info(f"Output saved to {output_file}")
            logger.info(f"Total items: {len(results)}")
            
            # Print summary statistics
            callback_count = sum(1 for item in results if item.get('item_type') == 'preamble_callback')
            ref_count = len(results) - callback_count
            logger.info(f"Callback items: {callback_count}")
            logger.info(f"Reference items: {ref_count}")
        else:
            logger.error("Failed to save output file")
    else:
        logger.warning("No data extracted from XML file")

if __name__ == "__main__":
    main()

