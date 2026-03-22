from typing import List, Dict
import random
import re

class QuizGenerator:
    """Generate quiz questions from PDF content"""
    
    def __init__(self):
        self.question_types = [
            'multiple_choice',
            'true_false',
            'fill_blank',
            'short_answer'
        ]
    
    def generate_quiz(self, chunks: List[Dict], num_questions: int = 10, grade: str = None) -> List[Dict]:
        """
        Generate quiz questions from textbook chunks
        """
        
        # Filter by grade if specified
        if grade:
            chunks = [c for c in chunks if c.get("grade") == grade]
        
        if not chunks:
            return []
        
        questions = []
        used_content = set()
        
        # Generate different types of questions
        for i in range(num_questions):
            # Select random chunk that hasn't been used
            available_chunks = [c for c in chunks if c.get('chunk_id') not in used_content]
            if not available_chunks:
                # Reset if we've used all chunks
                used_content.clear()
                available_chunks = chunks
            
            chunk = random.choice(available_chunks)
            used_content.add(chunk.get('chunk_id'))
            
            # Generate question based on content
            question = self._generate_question_from_chunk(chunk, i + 1)
            if question:
                questions.append(question)
        
        return questions[:num_questions]
    
    def _generate_question_from_chunk(self, chunk: Dict, question_num: int) -> Dict:
        """
        Generate a single question from a chunk
        """
        content = chunk.get('content', '')
        chapter = chunk.get('chapter', 'General')
        
        # Extract key information from content
        sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 20]
        
        if not sentences:
            return None
        
        # Choose question type based on content
        question_type = self._choose_question_type(content)
        
        if question_type == 'multiple_choice':
            return self._generate_multiple_choice(sentences, chapter, question_num)
        elif question_type == 'true_false':
            return self._generate_true_false(sentences, chapter, question_num)
        elif question_type == 'fill_blank':
            return self._generate_fill_blank(sentences, chapter, question_num)
        else:
            return self._generate_short_answer(sentences, chapter, question_num)
    
    def _choose_question_type(self, content: str) -> str:
        """
        Choose appropriate question type based on content
        """
        content_lower = content.lower()
        
        # Multiple choice for definitions and concepts
        if any(word in content_lower for word in ['is used to', 'means', 'refers to', 'is a', 'are']):
            return 'multiple_choice'
        
        # True/false for statements
        if any(word in content_lower for word in ['always', 'never', 'all', 'every', 'only']):
            return 'true_false'
        
        # Fill in blank for commands and procedures
        if any(word in content_lower for word in ['command', 'syntax', 'use the', 'type']):
            return 'fill_blank'
        
        # Default to multiple choice
        return 'multiple_choice'
    
    def _generate_multiple_choice(self, sentences: List[str], chapter: str, question_num: int) -> Dict:
        """
        Generate multiple choice question
        """
        # Find a sentence with clear information
        base_sentence = None
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in [
                'is used to', 'means', 'refers to', 'is a', 'command', 'allows'
            ]):
                base_sentence = sentence
                break
        
        if not base_sentence:
            base_sentence = sentences[0]
        
        # Extract key terms
        key_terms = self._extract_key_terms(base_sentence)
        
        if not key_terms:
            return None
        
        # Create question by removing a key term
        key_term = random.choice(key_terms)
        question_text = base_sentence.replace(key_term, "______")
        
        # Generate options
        correct_answer = key_term
        wrong_options = self._generate_wrong_options(key_term, chapter)
        
        options = [correct_answer] + wrong_options[:3]
        random.shuffle(options)
        
        correct_index = options.index(correct_answer)
        
        return {
            'id': f'q_{question_num}',
            'type': 'multiple_choice',
            'question': f"Q{question_num}. Fill in the blank: {question_text}",
            'options': options,
            'correct_answer': correct_answer,
            'explanation': f"The correct answer is '{correct_answer}' as stated in the textbook.",
            'chapter': chapter,
            'points': 10
        }
    
    def _generate_true_false(self, sentences: List[str], chapter: str, question_num: int) -> Dict:
        """
        Generate true/false question
        """
        base_sentence = random.choice(sentences[:3])
        
        # Randomly make it true or false
        is_true = random.choice([True, False])
        
        if is_true:
            question_text = base_sentence
            correct_answer = True
            explanation = "This statement is true according to the textbook."
        else:
            # Modify sentence to make it false
            modified_sentence = self._modify_sentence_to_false(base_sentence)
            question_text = modified_sentence
            correct_answer = False
            explanation = "This statement is false. " + base_sentence
        
        return {
            'id': f'q_{question_num}',
            'type': 'true_false',
            'question': f"Q{question_num}. True or False: {question_text}",
            'correct_answer': correct_answer,
            'explanation': explanation,
            'chapter': chapter,
            'points': 10
        }
    
    def _generate_fill_blank(self, sentences: List[str], chapter: str, question_num: int) -> Dict:
        """
        Generate fill in the blank question
        """
        # Find sentence with commands or technical terms
        command_sentence = None
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['command', 'use', 'type', 'run', 'execute']):
                command_sentence = sentence
                break
        
        if not command_sentence:
            command_sentence = sentences[0]
        
        # Find technical terms to blank out
        technical_terms = re.findall(r'\b[a-zA-Z]+\b', command_sentence)
        important_terms = [term for term in technical_terms if len(term) > 3 and term.lower() not in [
            'the', 'and', 'for', 'with', 'this', 'that', 'from', 'they', 'have', 'will'
        ]]
        
        if not important_terms:
            return None
        
        blank_term = random.choice(important_terms)
        question_text = command_sentence.replace(blank_term, "______", 1)
        
        return {
            'id': f'q_{question_num}',
            'type': 'fill_blank',
            'question': f"Q{question_num}. Fill in the blank: {question_text}",
            'correct_answer': blank_term.lower(),
            'explanation': f"The correct answer is '{blank_term}'.",
            'chapter': chapter,
            'points': 10
        }
    
    def _generate_short_answer(self, sentences: List[str], chapter: str, question_num: int) -> Dict:
        """
        Generate short answer question
        """
        # Create a "what is" or "how to" question
        base_sentence = sentences[0]
        
        # Extract main concept
        concepts = self._extract_key_terms(base_sentence)
        
        if concepts:
            concept = concepts[0]
            question_text = f"What is {concept} used for?"
            sample_answer = base_sentence
        else:
            question_text = f"Explain the concept described in this chapter."
            sample_answer = base_sentence
        
        return {
            'id': f'q_{question_num}',
            'type': 'short_answer',
            'question': f"Q{question_num}. {question_text}",
            'sample_answer': sample_answer,
            'explanation': f"Sample answer: {sample_answer}",
            'chapter': chapter,
            'points': 15
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract important technical terms from text
        """
        # Common technical terms in Unix/Linux context
        technical_patterns = [
            r'\b(?:directory|file|folder|command|syntax|option|flag|parameter)\b',
            r'\b(?:ls|cd|mkdir|rmdir|cp|mv|rm|find|grep|chmod|tree|tar)\b',
            r'\b(?:system|structure|hierarchy|permission|backup|archive)\b'
        ]
        
        terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.extend(matches)
        
        # Also extract capitalized words (likely important terms)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        terms.extend(capitalized)
        
        return list(set(terms))
    
    def _generate_wrong_options(self, correct_term: str, chapter: str) -> List[str]:
        """
        Generate plausible wrong options for multiple choice
        """
        # Common wrong options based on context
        unix_commands = ['ls', 'cd', 'mkdir', 'rmdir', 'cp', 'mv', 'rm', 'find', 'grep', 'chmod', 'tree', 'tar', 'cat', 'less', 'head', 'tail']
        file_terms = ['directory', 'file', 'folder', 'path', 'link', 'inode', 'partition', 'disk']
        system_terms = ['process', 'service', 'daemon', 'kernel', 'shell', 'terminal', 'console']
        
        all_options = unix_commands + file_terms + system_terms
        
        # Remove the correct answer if it's in the list
        wrong_options = [opt for opt in all_options if opt.lower() != correct_term.lower()]
        
        # Add some generic wrong options
        generic_wrong = ['option1', 'option2', 'option3', 'none of the above']
        wrong_options.extend(generic_wrong)
        
        return random.sample(wrong_options, min(3, len(wrong_options)))
    
    def _modify_sentence_to_false(self, sentence: str) -> str:
        """
        Modify a sentence to make it false
        """
        # Simple modifications to make statements false
        modifications = [
            ('is used to', 'is not used to'),
            ('can', 'cannot'),
            ('allows', 'prevents'),
            ('creates', 'deletes'),
            ('displays', 'hides'),
            ('shows', 'hides'),
            ('enables', 'disables')
        ]
        
        for original, replacement in modifications:
            if original in sentence.lower():
                return sentence.lower().replace(original, replacement)
        
        # If no modification possible, add "not" somewhere
        if ' is ' in sentence:
            return sentence.replace(' is ', ' is not ')
        elif ' are ' in sentence:
            return sentence.replace(' are ', ' are not ')
        else:
            return f"It is not true that {sentence.lower()}"
    
    def calculate_score(self, answers: Dict, questions: List[Dict]) -> Dict:
        """
        Calculate quiz score and provide feedback
        """
        total_points = 0
        earned_points = 0
        correct_answers = 0
        feedback = []
        
        for question in questions:
            q_id = question['id']
            total_points += question['points']
            
            if q_id in answers:
                user_answer = answers[q_id]
                
                if question['type'] == 'multiple_choice':
                    if user_answer == question['correct_answer']:
                        earned_points += question['points']
                        correct_answers += 1
                        feedback.append({
                            'question_id': q_id,
                            'correct': True,
                            'explanation': question['explanation']
                        })
                    else:
                        feedback.append({
                            'question_id': q_id,
                            'correct': False,
                            'explanation': question['explanation'],
                            'correct_answer': question['correct_answer']
                        })
                
                elif question['type'] == 'true_false':
                    if user_answer == question['correct_answer']:
                        earned_points += question['points']
                        correct_answers += 1
                        feedback.append({
                            'question_id': q_id,
                            'correct': True,
                            'explanation': question['explanation']
                        })
                    else:
                        feedback.append({
                            'question_id': q_id,
                            'correct': False,
                            'explanation': question['explanation']
                        })
                
                elif question['type'] == 'fill_blank':
                    if user_answer.lower().strip() == question['correct_answer'].lower().strip():
                        earned_points += question['points']
                        correct_answers += 1
                        feedback.append({
                            'question_id': q_id,
                            'correct': True,
                            'explanation': question['explanation']
                        })
                    else:
                        feedback.append({
                            'question_id': q_id,
                            'correct': False,
                            'explanation': question['explanation'],
                            'correct_answer': question['correct_answer']
                        })
                
                elif question['type'] == 'short_answer':
                    # Simple keyword matching for short answers
                    sample_words = set(question['sample_answer'].lower().split())
                    user_words = set(user_answer.lower().split())
                    
                    # If user answer contains key concepts, give partial credit
                    overlap = len(sample_words.intersection(user_words))
                    if overlap >= len(sample_words) * 0.3:  # 30% overlap
                        earned_points += question['points']
                        correct_answers += 1
                        feedback.append({
                            'question_id': q_id,
                            'correct': True,
                            'explanation': question['explanation']
                        })
                    else:
                        feedback.append({
                            'question_id': q_id,
                            'correct': False,
                            'explanation': question['explanation'],
                            'sample_answer': question['sample_answer']
                        })
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return {
            'total_questions': len(questions),
            'correct_answers': correct_answers,
            'total_points': total_points,
            'earned_points': earned_points,
            'percentage': round(percentage, 1),
            'grade': self._get_letter_grade(percentage),
            'feedback': feedback
        }
    
    def _get_letter_grade(self, percentage: float) -> str:
        """
        Convert percentage to letter grade
        """
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'