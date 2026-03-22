from typing import List, Dict
import re

class ContextPruner:
    """Advanced context pruning to find most relevant PDF content for questions"""
    
    def __init__(self):
        self.max_context_tokens = 3000  # Increased for more comprehensive content
    
    def find_relevant_chunks(
        self,
        question: str,
        chunks: List[Dict],
        grade: str = None
    ) -> List[Dict]:
        """
        Find most relevant textbook chunks for the question
        Uses advanced semantic matching and scoring
        """
        
        # Extract keywords and concepts from question
        keywords = self._extract_keywords(question)
        concepts = self._extract_concepts(question)
        question_type = self._identify_question_type(question)
        
        # Filter by grade if specified
        if grade:
            chunks = [c for c in chunks if c.get("grade") == grade]
        
        # Score each chunk with advanced matching
        scored_chunks = []
        for chunk in chunks:
            score = self._advanced_score_chunk(chunk, keywords, concepts, question_type, question)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score (highest first)
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        
        # Return top chunks (more chunks for comprehensive analysis)
        return [chunk for score, chunk in scored_chunks[:12]]
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract technical concepts and important terms"""
        # Look for technical terms, commands, and concepts
        concepts = []
        
        # Unix/Linux commands
        unix_commands = re.findall(r'\b(?:ls|cd|mkdir|rmdir|cp|mv|rm|find|grep|chmod|chown|tar|gzip|cat|less|more|head|tail|sort|uniq|wc|diff|tree|pwd|whoami|ps|kill|top|df|du|mount|umount|ln|touch|file|which|whereis|locate|updatedb|crontab|at|jobs|bg|fg|nohup|screen|tmux|ssh|scp|rsync|wget|curl|ping|netstat|ifconfig|iptables|systemctl|service|sudo|su|passwd|useradd|userdel|usermod|groupadd|groupdel|id|groups|history|alias|export|env|set|unset|source|bash|sh|zsh|awk|sed|cut|tr|xargs|tee|pipe)\b', text.lower())
        concepts.extend(unix_commands)
        
        # File system concepts
        fs_concepts = re.findall(r'\b(?:directory|folder|file|path|permission|owner|group|executable|readable|writable|symbolic|link|hardlink|inode|filesystem|mount|partition|disk|backup|archive|compression|hierarchy|structure|tree|root|home|bin|etc|var|tmp|usr|opt|proc|sys|dev|mnt|media)\b', text.lower())
        concepts.extend(fs_concepts)
        
        # Programming concepts
        prog_concepts = re.findall(r'\b(?:script|scripting|shell|bash|variable|function|loop|condition|if|else|then|fi|for|while|do|done|case|esac|return|exit|echo|print|read|input|output|pipe|redirect|stdout|stderr|stdin)\b', text.lower())
        concepts.extend(prog_concepts)
        
        # System administration
        admin_concepts = re.findall(r'\b(?:system|administration|user|group|security|network|process|service|daemon|log|configuration|config|install|package|repository|update|upgrade|kernel|boot|startup|shutdown|cron|schedule|task|job|monitoring|performance|memory|cpu|disk|space|usage)\b', text.lower())
        concepts.extend(admin_concepts)
        
        return list(set(concepts))  # Remove duplicates
    
    def _identify_question_type(self, question: str) -> str:
        """Identify the type of question being asked"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['how to', 'how do', 'how can', 'steps to', 'procedure']):
            return 'how_to'
        elif any(word in question_lower for word in ['what is', 'what are', 'define', 'definition', 'meaning']):
            return 'definition'
        elif any(word in question_lower for word in ['why', 'reason', 'purpose', 'benefit', 'advantage']):
            return 'explanation'
        elif any(word in question_lower for word in ['list', 'show', 'display', 'enumerate']):
            return 'listing'
        elif any(word in question_lower for word in ['command', 'syntax', 'option', 'flag', 'parameter']):
            return 'command'
        elif any(word in question_lower for word in ['example', 'sample', 'demonstrate']):
            return 'example'
        elif any(word in question_lower for word in ['difference', 'compare', 'vs', 'versus']):
            return 'comparison'
        else:
            return 'general'
    
    def _advanced_score_chunk(self, chunk: Dict, keywords: List[str], concepts: List[str], question_type: str, original_question: str) -> float:
        """Advanced scoring with semantic understanding"""
        content = chunk.get("content", "").lower()
        chapter = chunk.get("chapter", "").lower()
        
        score = 0.0
        
        # 1. Keyword matching (basic score)
        for keyword in keywords:
            count = content.count(keyword)
            score += count * 1.0
        
        # 2. Concept matching (higher weight)
        for concept in concepts:
            count = content.count(concept)
            score += count * 2.0
        
        # 3. Question type specific scoring
        if question_type == 'how_to':
            # Look for procedural language
            procedural_words = ['step', 'first', 'then', 'next', 'finally', 'procedure', 'process', 'method']
            for word in procedural_words:
                if word in content:
                    score += 3.0
        
        elif question_type == 'definition':
            # Look for definitional language
            def_words = ['is', 'are', 'means', 'refers to', 'defined as', 'definition']
            for word in def_words:
                if word in content:
                    score += 2.5
        
        elif question_type == 'command':
            # Look for command syntax and examples
            if any(cmd in content for cmd in ['$', '#', 'command', 'syntax', 'option', 'flag']):
                score += 4.0
        
        elif question_type == 'example':
            # Look for examples
            example_words = ['example', 'sample', 'for instance', 'such as', 'like']
            for word in example_words:
                if word in content:
                    score += 3.5
        
        # 4. Chapter relevance
        question_lower = original_question.lower()
        if any(word in chapter for word in question_lower.split()):
            score += 2.0
        
        # 5. Content length bonus (prefer substantial content)
        content_length = len(content)
        if 200 <= content_length <= 1000:  # Sweet spot for informative content
            score += 1.0
        elif content_length > 1000:
            score += 0.5
        
        # 6. Exact phrase matching (highest weight)
        question_phrases = self._extract_phrases(original_question)
        for phrase in question_phrases:
            if phrase.lower() in content:
                score += 5.0
        
        return score
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract important phrases from text"""
        # Look for quoted phrases or technical terms
        phrases = []
        
        # Quoted phrases
        quoted = re.findall(r'"([^"]*)"', text)
        phrases.extend(quoted)
        
        # Technical phrases (2-3 words)
        words = text.split()
        for i in range(len(words) - 1):
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                phrase = f"{words[i]} {words[i+1]}"
                if not any(stop in phrase.lower() for stop in ['what is', 'how to', 'why does']):
                    phrases.append(phrase)
        
        return phrases
    
    def prune_context(self, chunks: List[Dict], max_tokens: int = 3000) -> str:
        """
        Combine and prune chunks to fit within token limit
        Prioritizes most relevant content with student-friendly formatting
        """
        
        if not chunks:
            return "No relevant information found in your textbook for this question."
        
        combined_text = ""
        current_tokens = 0
        
        for chunk in chunks:
            content = chunk.get("content", "")
            chunk_tokens = self._estimate_tokens(content)
            
            if current_tokens + chunk_tokens <= max_tokens:
                # Add full chunk with student-friendly formatting
                chapter = chunk.get("chapter", "")
                if chapter and chapter not in combined_text:
                    combined_text += f"\n\n📚 From Chapter: {chapter}\n{content}"
                else:
                    combined_text += f"\n\n{content}"
                current_tokens += chunk_tokens
            else:
                # Add partial chunk to fill remaining space
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # Only add if meaningful space left
                    partial_content = self._truncate_to_tokens(content, remaining_tokens)
                    combined_text += f"\n\n{partial_content}..."
                break
        
        return combined_text.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common words but keep technical terms
        stop_words = {
            'what', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'how', 'why', 'when',
            'where', 'which', 'who', 'can', 'could', 'would', 'should', 'do', 'does',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Tokenize and clean
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _score_chunk(self, chunk: Dict, keywords: List[str]) -> float:
        """Score chunk relevance based on keyword matches"""
        content = chunk.get("content", "").lower()
        
        score = 0.0
        for keyword in keywords:
            # Count occurrences
            count = content.count(keyword)
            score += count
        
        return score
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximate token limit"""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        
        # Truncate at sentence boundary if possible
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        
        if last_period > max_chars * 0.8:  # If period is in last 20%
            return truncated[:last_period + 1]
        
        return truncated
