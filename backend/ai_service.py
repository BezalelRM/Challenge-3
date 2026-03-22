import httpx
from typing import Dict
import os
import re

class AIService:
    """
    Complete AI Tutoring Pipeline:
    1. ScaleDown - Compress context (90% token reduction)
    2. Gemini 2.5 Flash - Generate answers (FREE tier)
    
    This is the ONLY way to use ScaleDown - it compresses, then you need an LLM.
    """
    
    def __init__(self):
        # ScaleDown for compression
        self.compress_url = "https://api.scaledown.xyz/compress/raw"
        self.scaledown_key = "Dl2BOqfiIr6aTZQjeDulY9cWDTih7ijp6C0l4U7G"
        
        # Gemini 2.5 Flash (FREE tier - ScaleDown's supported model)
        # Get free key at: https://aistudio.google.com/apikey
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        self.timeout = 90.0  # Increased timeout for longer processing
    
    async def get_compressed_answer(
        self,
        context: str,
        question: str,
        model: str = "gemini-2.5-flash"
    ) -> Dict:
        """
        Two-step process (as per ScaleDown documentation):
        1. Compress context with ScaleDown
        2. Generate answer with Gemini (ScaleDown's supported model)
        """
        
        # Step 1: Compress using ScaleDown
        compress_payload = {
            "context": context,
            "prompt": question,
            "model": model,  # Target model for compression optimization
            "scaledown": {
                "rate": "auto"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Compress the context
                compress_response = await client.post(
                    self.compress_url,
                    json=compress_payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.scaledown_key
                    }
                )
                
                print(f"ScaleDown Status: {compress_response.status_code}")
                
                if compress_response.status_code == 200:
                    compress_data = compress_response.json()
                    
                    # Extract compression results
                    results = compress_data.get("results", {})
                    compressed_context = results.get("compressed_prompt", context)
                    original_tokens = results.get("original_prompt_tokens", 0)
                    compressed_tokens = results.get("compressed_prompt_tokens", 0)
                    compression_ratio = results.get("compression_ratio", 0)
                    compression_rate = compression_ratio * 100
                    
                    print(f"✅ ScaleDown Compression: {original_tokens} → {compressed_tokens} tokens ({compression_rate:.1f}% saved)")
                    
                    # Step 2: Generate answer with Gemini using compressed context
                    if self.gemini_key:
                        answer = await self._call_gemini(client, compressed_context, question)
                        
                        return {
                            "answer": answer,
                            "original_tokens": original_tokens,
                            "compressed_tokens": compressed_tokens,
                            "compression_rate": round(compression_rate, 2)
                        }
                    else:
                        # No Gemini key - return compressed textbook content
                        compressed_answer = self._extract_key_answer(compressed_context)
                        compressed_tokens_actual = self.estimate_tokens(compressed_answer)
                        
                        return {
                            "answer": f"""📚 **Answer:**

{compressed_answer}""",
                            "original_tokens": original_tokens,
                            "compressed_tokens": compressed_tokens_actual,
                            "compression_rate": round(((original_tokens - compressed_tokens_actual) / original_tokens) * 100, 2) if original_tokens > 0 else 0
                        }
                
                else:
                    # ScaleDown failed - use original context without compression
                    print(f"⚠️ ScaleDown failed (Status: {compress_response.status_code}), using original context")
                    
                    # Estimate tokens for the original context
                    original_tokens = self.estimate_tokens(context)
                    
                    # Truncate context if too long (keep first 2000 characters)
                    truncated_context = context[:2000] if len(context) > 2000 else context
                    
                    # If we have Gemini key, try with original context
                    if self.gemini_key:
                        answer = await self._call_gemini(client, truncated_context, question)
                        
                        return {
                            "answer": answer,
                            "original_tokens": original_tokens,
                            "compressed_tokens": original_tokens,  # No compression
                            "compression_rate": 0
                        }
                    else:
                        # No Gemini key - return compressed textbook content directly
                        compressed_answer = self._extract_key_answer(truncated_context)
                        compressed_tokens_actual = self.estimate_tokens(compressed_answer)
                        
                        return {
                            "answer": f"""📚 **Answer:**

{compressed_answer}""",
                            "original_tokens": original_tokens,
                            "compressed_tokens": compressed_tokens_actual,
                            "compression_rate": round(((original_tokens - compressed_tokens_actual) / original_tokens) * 100, 2) if original_tokens > 0 else 0
                        }
        
        except Exception as e:
            print(f"⚠️ ScaleDown error: {str(e)}, using original context")
            
            # Fallback: use original context without compression
            original_tokens = self.estimate_tokens(context)
            
            # Truncate context if too long (keep first 2000 characters)
            truncated_context = context[:2000] if len(context) > 2000 else context
            
            # If we have Gemini key, try with original context
            if self.gemini_key:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                        answer = await self._call_gemini(client, truncated_context, question)
                        
                        return {
                            "answer": answer,
                            "original_tokens": original_tokens,
                            "compressed_tokens": original_tokens,  # No compression
                            "compression_rate": 0
                        }
                except Exception as gemini_error:
                    print(f"Gemini fallback also failed: {str(gemini_error)}")
            
            # Final fallback - return compressed textbook content directly
            compressed_answer = self._extract_key_answer(truncated_context)
            compressed_tokens_actual = self.estimate_tokens(compressed_answer)
            
            return {
                "answer": f"""📚 **Answer:**

{compressed_answer}""",
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens_actual,
                "compression_rate": round(((original_tokens - compressed_tokens_actual) / original_tokens) * 100, 2) if original_tokens > 0 else 0
            }
    
    async def _call_gemini(self, client: httpx.AsyncClient, compressed_context: str, question: str) -> str:
        """
        Call Gemini 2.5 Flash with compressed context
        This is ScaleDown's recommended approach
        """
        
        gemini_payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are a friendly and helpful tutor who explains things in a simple, easy-to-understand way. Your goal is to help students learn by making complex topics clear and engaging.

TEXTBOOK CONTENT:
{compressed_context}

STUDENT QUESTION: {question}

INSTRUCTIONS:
1. Write in a conversational, friendly tone as if you're talking to a student face-to-face
2. Break down complex concepts into simple, digestible parts
3. Use everyday language while keeping technical terms when necessary (but explain them)
4. Give practical examples and analogies when helpful
5. Structure your answer clearly with bullet points or numbered steps when appropriate
6. Be encouraging and supportive in your tone
7. If there are commands or procedures, explain what they do in plain English
8. Make the content engaging and easy to remember

RESPONSE STYLE:
- Start with a friendly greeting or acknowledgment
- Use "you" to address the student directly
- Include encouraging phrases like "Here's how it works..." or "Let me break this down for you..."
- End with a helpful summary or next steps

ANSWER:"""
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,  # Slightly higher for more natural language
                "maxOutputTokens": 400,  # Longer for detailed friendly explanations
                "topP": 0.9
            }
        }
        
        try:
            gemini_response = await client.post(
                f"{self.gemini_url}?key={self.gemini_key}",
                json=gemini_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Gemini Status: {gemini_response.status_code}")
            
            if gemini_response.status_code == 200:
                gemini_data = gemini_response.json()
                candidates = gemini_data.get("candidates", [])
                
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        answer = parts[0].get("text", "").strip()
                        print("✅ Answer generated via Gemini")
                        return answer
            
            return f"❌ Gemini API error (Status: {gemini_response.status_code})"
        
        except Exception as e:
            return f"❌ Gemini error: {str(e)}"
    
    def _get_setup_instructions(self, compressed_context: str, compression_rate: float, original_tokens: int, compressed_tokens: int) -> str:
        """
        Return clean, concise textbook content
        """
        
        # Force compression by extracting only the key information
        simplified_content = self._extract_key_answer(compressed_context)
        
        return f"""📚 **Answer:**

{simplified_content}"""
    
    def _extract_key_answer(self, content: str) -> str:
        """
        Extract student-friendly answer from content
        """
        # Remove chapter markers and clean up
        content = content.replace('[Chapter: General]', '').strip()
        content = ' '.join(content.split())  # Remove extra whitespace
        
        # Split into sentences
        sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 10]
        
        if not sentences:
            return "I couldn't find specific information about that in your textbook. Could you try asking in a different way?"
        
        # Create a friendly, conversational response
        friendly_sections = []
        
        # Start with a friendly greeting
        greeting = "Great question! Let me help you understand this. 😊"
        
        # Section 1: Simple explanation
        definition_sentences = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in [
                'is defined as', 'refers to', 'means', 'is a', 'are used to',
                'is used to', 'allows you to', 'enables', 'purpose is'
            ]):
                definition_sentences.append(sentence)
        
        if definition_sentences:
            friendly_sections.append(f"**Here's what it means:** {definition_sentences[0]}.")
        
        # Section 2: How it works (commands/procedures)
        procedure_sentences = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in [
                'command', 'syntax', 'to create', 'to display', 'to find',
                'use the', 'run the', 'execute', 'type', 'enter'
            ]):
                procedure_sentences.append(sentence)
        
        if procedure_sentences:
            friendly_sections.append(f"**How it works:** {procedure_sentences[0]}.")
        
        # Section 3: Practical examples
        example_sentences = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in [
                'example', 'for instance', 'such as', 'like', 'including'
            ]):
                example_sentences.append(sentence)
        
        if example_sentences:
            friendly_sections.append(f"**For example:** {example_sentences[0]}.")
        
        # If no structured content found, provide a simple overview
        if not friendly_sections:
            # Take the most informative sentences and make them friendly
            informative_sentences = [s for s in sentences[:3] if len(s) > 20]
            if informative_sentences:
                friendly_sections.append(f"**Here's what your textbook says:** {'. '.join(informative_sentences[:2])}.")
        
        # Combine with friendly tone
        if friendly_sections:
            result = f"{greeting}\n\n" + '\n\n'.join(friendly_sections)
            result += "\n\n💡 **Need more help?** Feel free to ask me to explain any part in more detail!"
        else:
            result = f"{greeting}\n\nBased on your textbook: {'. '.join(sentences[:2])}.\n\n💡 **Want me to break this down further?** Just ask!"
        
        # Clean up the response
        result = self._clean_answer(result)
        
        # Keep it concise but helpful (up to 400 characters)
        if len(result) > 400:
            result = result[:397] + "..."
        
        return result
    
    def _clean_answer(self, answer: str) -> str:
        """
        Clean up the answer text for better readability
        """
        # Remove redundant phrases
        answer = answer.strip()
        
        # Fix common formatting issues
        answer = re.sub(r'\s+', ' ', answer)  # Multiple spaces
        answer = re.sub(r'([.!?])\s*([.!?])', r'\1', answer)  # Multiple punctuation
        
        # Ensure proper sentence ending
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        return answer
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
