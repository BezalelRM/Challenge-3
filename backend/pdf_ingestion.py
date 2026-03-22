from typing import List, Dict
import re
import sys

print(f"Python path: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
    print("✅ pdfplumber loaded successfully")
except ImportError as e:
    PDFPLUMBER_AVAILABLE = False
    print(f"❌ pdfplumber import failed: {e}")

try:
    import PyPDF2
    from io import BytesIO
    PYPDF2_AVAILABLE = True
    print("✅ PyPDF2 loaded successfully")
except ImportError as e:
    PYPDF2_AVAILABLE = False
    print(f"❌ PyPDF2 import failed: {e}")

class PDFIngestion:
    """Extract and chunk textbook PDFs with multiple extraction methods"""
    
    def __init__(self):
        self.chunk_size = 1000  # Characters per chunk
        self.overlap = 200  # Overlap between chunks
    
    def process_pdf(self, pdf_content: bytes, grade: str = "10") -> List[Dict]:
        """
        Extract text from PDF using pdfplumber (preferred) or PyPDF2 (fallback)
        """
        
        # Try pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                return self._process_with_pdfplumber(pdf_content, grade)
            except Exception as e:
                print(f"pdfplumber failed: {str(e)}, trying PyPDF2...")
        
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                return self._process_with_pypdf2(pdf_content, grade)
            except Exception as e:
                raise Exception(f"Both PDF extraction methods failed. Error: {str(e)}")
        
        raise Exception("No PDF processing library available. Install pdfplumber or PyPDF2.")
    
    def _process_with_pdfplumber(self, pdf_content: bytes, grade: str) -> List[Dict]:
        """Extract text using pdfplumber (better quality)"""
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_content)
        
        print("Using pdfplumber for text extraction...")
        
        full_text = ""
        valid_pages = 0
        
        with pdfplumber.open(pdf_file) as pdf:
            print(f"Processing PDF with {len(pdf.pages)} pages...")
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract text with better handling
                    page_text = page.extract_text()
                    
                    # More lenient validation - accept any page with some text
                    if page_text and len(page_text.strip()) > 10:  # Reduced from 50 to 10
                        full_text += page_text + "\n\n"
                        valid_pages += 1
                    else:
                        print(f"Skipping page {page_num + 1}: empty or too short")
                        
                except Exception as e:
                    print(f"Error extracting page {page_num + 1}: {str(e)}")
                    continue
        
        print(f"Successfully extracted text from {valid_pages} pages using pdfplumber")
        
        if not full_text.strip():
            raise Exception("No readable text could be extracted. The PDF may be scanned or image-based.")
        
        return self._process_extracted_text(full_text, grade)
    
    def _process_with_pypdf2(self, pdf_content: bytes, grade: str) -> List[Dict]:
        """Extract text using PyPDF2 (fallback)"""
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        print("Using PyPDF2 for text extraction...")
        print(f"Processing PDF with {len(pdf_reader.pages)} pages...")
        
        full_text = ""
        valid_pages = 0
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                
                # More lenient validation
                if page_text and len(page_text.strip()) > 10:  # Reduced from 50 to 10
                    full_text += page_text + "\n"
                    valid_pages += 1
                else:
                    print(f"Skipping page {page_num + 1}: empty or too short")
                    
            except Exception as e:
                print(f"Error extracting page {page_num + 1}: {str(e)}")
                continue
        
        print(f"Successfully extracted text from {valid_pages} pages using PyPDF2")
        
        if not full_text.strip():
            raise Exception("No readable text could be extracted. The PDF may be scanned or image-based.")
        
        return self._process_extracted_text(full_text, grade)
    
    def _process_extracted_text(self, full_text: str, grade: str) -> List[Dict]:
        """Process extracted text into chunks"""
        
        # STRICT CHECK: Detect CID font codes before any processing
        cid_pattern = r'\(cid:\d+\)'
        cid_matches = re.findall(cid_pattern, full_text)
        
        # If we find ANY CID codes, reject the PDF immediately
        if len(cid_matches) > 10:  # More than 10 CID codes = unreadable PDF
            raise Exception(
                "⚠️ PDF CONTAINS UNREADABLE TEXT\n\n"
                f"This PDF contains {len(cid_matches)} CID font codes, which means the text cannot be extracted properly. "
                "CID codes like (cid:16)(cid:17)(cid:18) indicate the PDF uses custom/embedded fonts or is scanned.\n\n"
                "SOLUTIONS:\n"
                "1. Convert the PDF using an OCR tool (like Adobe Acrobat OCR)\n"
                "2. Use 'Save As' in Adobe Acrobat to create a new PDF with standard fonts\n"
                "3. Try an online PDF to text converter that supports OCR\n"
                "4. If you have the original document, export it again with standard fonts\n\n"
                "The system cannot process this PDF in its current format."
            )
        
        # Check if text is mostly unreadable after cleaning
        cleaned_sample = self._clean_text(full_text[:5000])  # Check first 5000 chars
        if len(cleaned_sample) < 100:
            raise Exception(
                "⚠️ PDF TEXT EXTRACTION ISSUE\n\n"
                "The PDF appears to use custom fonts or encoding that cannot be extracted as readable text. "
                "This commonly happens with:\n"
                "- Scanned documents (images of text)\n"
                "- PDFs with custom/embedded fonts\n"
                "- PDFs created from certain design software\n\n"
                "SOLUTIONS:\n"
                "1. Try converting the PDF to text using an OCR tool first\n"
                "2. Use Adobe Acrobat to 'Save As' a new PDF with standard fonts\n"
                "3. Copy-paste the text content into a new document\n"
                "4. Use an online PDF to text converter that supports OCR\n\n"
                "If you believe this is an error, please try a different PDF file."
            )
        
        # Detect chapters
        chapters = self._detect_chapters(full_text)
        
        # Create chunks
        chunks = []
        
        if chapters:
            print(f"Detected {len(chapters)} chapters")
            for chapter_name, chapter_text in chapters.items():
                chapter_chunks = self._create_chunks(chapter_text, chapter_name, grade)
                chunks.extend(chapter_chunks)
        else:
            print("No chapters detected, processing as single document")
            chunks = self._create_chunks(full_text, "General", grade)
        
        if not chunks:
            raise Exception(
                "⚠️ NO VALID CONTENT EXTRACTED\n\n"
                "After processing, no readable content chunks could be created. "
                "The PDF may contain mostly images, tables, or use incompatible text encoding.\n\n"
                "Please try:\n"
                "1. A different PDF file\n"
                "2. Converting the PDF using OCR software\n"
                "3. Exporting the content to a text-based PDF format"
            )
        
        print(f"✅ Total valid chunks created: {len(chunks)}")
        return chunks
    
    def _detect_chapters(self, text: str) -> Dict[str, str]:
        """
        Detect chapter boundaries in text
        Looks for patterns like "Chapter 1", "CHAPTER 1:", etc.
        """
        
        # Pattern to match chapter headers
        chapter_pattern = r'(?:CHAPTER|Chapter)\s+(\d+|[IVX]+)[\s:.-]+(.*?)(?=(?:CHAPTER|Chapter)\s+(?:\d+|[IVX]+)|$)'
        
        matches = re.finditer(chapter_pattern, text, re.IGNORECASE | re.DOTALL)
        
        chapters = {}
        for match in matches:
            chapter_num = match.group(1)
            chapter_title = match.group(2).strip().split('\n')[0][:100]  # First line as title
            chapter_text = match.group(0)
            
            chapter_name = f"Chapter {chapter_num}: {chapter_title}"
            chapters[chapter_name] = chapter_text
        
        return chapters
    
    def _create_chunks(self, text: str, chapter: str, grade: str) -> List[Dict]:
        """
        Split text into overlapping chunks with validation
        """
        
        chunks = []
        text = self._clean_text(text)
        
        # Skip if cleaned text is too short or invalid
        if len(text) < 100:
            print(f"Warning: Chapter '{chapter}' has insufficient valid text after cleaning")
            return chunks
        
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for period followed by space
                period_pos = text.rfind('. ', start, end)
                if period_pos > start + self.chunk_size * 0.7:  # At least 70% of chunk
                    end = period_pos + 1
            
            chunk_text = text[start:end].strip()
            
            # Validate chunk before adding
            if chunk_text and self._is_valid_chunk(chunk_text):
                chunks.append({
                    "chapter": chapter,
                    "content": chunk_text,
                    "grade": grade,
                    "chunk_id": f"{chapter}_{chunk_id}",
                    "start_pos": start,
                    "end_pos": end
                })
                chunk_id += 1
            else:
                print(f"Skipping invalid chunk at position {start}-{end}")
            
            # Move start position with overlap
            start = end - self.overlap
        
        print(f"Created {len(chunks)} valid chunks for '{chapter}'")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text with balanced filtering"""
        
        # Remove CID codes (these indicate unreadable custom fonts)
        cid_pattern = r'\(cid:\d+\)'
        text = re.sub(cid_pattern, '', text)
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t ')
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove page numbers (standalone numbers at line ends)
        text = re.sub(r'\b\d{1,3}\b(?=\s*$)', '', text, flags=re.MULTILINE)
        
        # Remove repeated special characters (like multiple dots, dashes)
        text = re.sub(r'([.,;:!?\-])\1{3,}', r'\1', text)  # Changed from 2+ to 3+
        
        # Keep lines with at least some content
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # More lenient - keep lines with at least 5 characters
            if len(line) >= 5:
                # Count alphanumeric characters
                alpha_count = sum(c.isalnum() for c in line)
                total_count = len(line)
                
                # Keep line if at least 20% is alphanumeric (reduced from 40%)
                if total_count > 0 and (alpha_count / total_count) >= 0.2:
                    cleaned_lines.append(line)
        
        text = ' '.join(cleaned_lines)
        
        # Remove excessive spaces again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _is_valid_chunk(self, text: str) -> bool:
        """Check if chunk contains valid, readable text - more lenient validation"""
        if len(text) < 20:  # Reduced from 50 to 20
            return False
        
        # Count words (sequences of letters)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        
        # Need at least 5 valid words (reduced from 10)
        if len(words) < 5:
            return False
        
        # Check for reasonable character distribution
        alpha_count = sum(c.isalpha() for c in text)
        total_count = len(text)
        
        # At least 30% should be letters (reduced from 50%)
        if (alpha_count / total_count) < 0.3:
            return False
        
        return True
