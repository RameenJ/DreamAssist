# backend/services/fallback_questions.py
"""
Fallback diagnostic questions for common subjects.
Used when AI generation fails to ensure 100% reliability.
"""

import random
from typing import List, Dict, Any

FALLBACK_QUESTIONS = {
    "Mathematics": [
        {
            "question": "What is the derivative of x² with respect to x?",
            "options": ["2x", "x", "2", "x²"],
            "correct_answer": "2x"
        },
        {
            "question": "What is the value of sin(90°)?",
            "options": ["0", "1", "-1", "undefined"],
            "correct_answer": "1"
        },
        {
            "question": "If a triangle has angles 60°, 60°, and 60°, what type of triangle is it?",
            "options": ["Equilateral", "Isosceles", "Scalene", "Right-angled"],
            "correct_answer": "Equilateral"
        },
        {
            "question": "What is the quadratic formula for solving ax² + bx + c = 0?",
            "options": ["x = (-b ± √(b²-4ac)) / 2a", "x = -b / 2a", "x = b² - 4ac", "x = √(b²-4ac)"],
            "correct_answer": "x = (-b ± √(b²-4ac)) / 2a"
        },
        {
            "question": "What is the integral of 1/x with respect to x?",
            "options": ["ln|x| + C", "x² + C", "1/x² + C", "e^x + C"],
            "correct_answer": "ln|x| + C"
        },
        {
            "question": "What is the sum of angles in a triangle?",
            "options": ["180°", "360°", "90°", "270°"],
            "correct_answer": "180°"
        },
        {
            "question": "What is the Pythagorean theorem?",
            "options": ["a² + b² = c²", "a + b = c", "a² - b² = c²", "ab = c"],
            "correct_answer": "a² + b² = c²"
        }
    ],
    
    "Physics": [
        {
            "question": "What is Newton's second law of motion?",
            "options": ["F = ma", "E = mc²", "F = G(m1m2)/r²", "v = u + at"],
            "correct_answer": "F = ma"
        },
        {
            "question": "What is the SI unit of force?",
            "options": ["Newton", "Joule", "Watt", "Pascal"],
            "correct_answer": "Newton"
        },
        {
            "question": "What is the speed of light in vacuum?",
            "options": ["3 × 10⁸ m/s", "3 × 10⁶ m/s", "3 × 10¹⁰ m/s", "3 × 10⁵ m/s"],
            "correct_answer": "3 × 10⁸ m/s"
        },
        {
            "question": "What type of energy does a compressed spring have?",
            "options": ["Potential energy", "Kinetic energy", "Thermal energy", "Chemical energy"],
            "correct_answer": "Potential energy"
        },
        {
            "question": "What is the formula for kinetic energy?",
            "options": ["½mv²", "mgh", "mc²", "Fd"],
            "correct_answer": "½mv²"
        },
        {
            "question": "What happens to resistance when length of a wire increases?",
            "options": ["Increases", "Decreases", "Remains constant", "Becomes zero"],
            "correct_answer": "Increases"
        },
        {
            "question": "What is the unit of electric current?",
            "options": ["Ampere", "Volt", "Ohm", "Coulomb"],
            "correct_answer": "Ampere"
        }
    ],
    
    "Chemistry": [
        {
            "question": "What is the chemical formula for water?",
            "options": ["H₂O", "CO₂", "O₂", "H₂O₂"],
            "correct_answer": "H₂O"
        },
        {
            "question": "What is the pH of a neutral solution?",
            "options": ["7", "0", "14", "1"],
            "correct_answer": "7"
        },
        {
            "question": "What is Avogadro's number?",
            "options": ["6.022 × 10²³", "3.14 × 10²³", "9.8 × 10²³", "1.6 × 10²³"],
            "correct_answer": "6.022 × 10²³"
        },
        {
            "question": "What type of bond is formed when electrons are shared?",
            "options": ["Covalent bond", "Ionic bond", "Metallic bond", "Hydrogen bond"],
            "correct_answer": "Covalent bond"
        },
        {
            "question": "What is the atomic number of Carbon?",
            "options": ["6", "12", "8", "14"],
            "correct_answer": "6"
        },
        {
            "question": "What gas is produced when acid reacts with metal?",
            "options": ["Hydrogen", "Oxygen", "Carbon dioxide", "Nitrogen"],
            "correct_answer": "Hydrogen"
        },
        {
            "question": "What is the most abundant element in Earth's atmosphere?",
            "options": ["Nitrogen", "Oxygen", "Carbon dioxide", "Argon"],
            "correct_answer": "Nitrogen"
        }
    ],
    
    "Data Structures": [
        {
            "question": "What is the time complexity of accessing an element in an array by index?",
            "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
            "correct_answer": "O(1)"
        },
        {
            "question": "Which data structure uses LIFO (Last In First Out) principle?",
            "options": ["Stack", "Queue", "Linked List", "Tree"],
            "correct_answer": "Stack"
        },
        {
            "question": "What is the worst-case time complexity of Quick Sort?",
            "options": ["O(n²)", "O(n log n)", "O(n)", "O(log n)"],
            "correct_answer": "O(n²)"
        },
        {
            "question": "In a binary tree, what is the maximum number of children a node can have?",
            "options": ["2", "1", "3", "Unlimited"],
            "correct_answer": "2"
        },
        {
            "question": "Which traversal visits nodes in the order: left subtree, root, right subtree?",
            "options": ["Inorder", "Preorder", "Postorder", "Level-order"],
            "correct_answer": "Inorder"
        },
        {
            "question": "What is a hash collision?",
            "options": ["When two keys map to the same hash value", "When hash function fails", "When hash table is empty", "When key is null"],
            "correct_answer": "When two keys map to the same hash value"
        },
        {
            "question": "What is the space complexity of merge sort?",
            "options": ["O(n)", "O(1)", "O(log n)", "O(n²)"],
            "correct_answer": "O(n)"
        }
    ],
    
    "Programming": [
        {
            "question": "What does OOP stand for?",
            "options": ["Object-Oriented Programming", "Operator Overloading Protocol", "Output Operation Process", "Optimized Object Processor"],
            "correct_answer": "Object-Oriented Programming"
        },
        {
            "question": "Which of these is NOT a primitive data type in most programming languages?",
            "options": ["String", "Integer", "Boolean", "Character"],
            "correct_answer": "String"
        },
        {
            "question": "What is recursion?",
            "options": ["A function calling itself", "A loop structure", "A data type", "An error handling method"],
            "correct_answer": "A function calling itself"
        },
        {
            "question": "What is the purpose of a constructor in OOP?",
            "options": ["Initialize object properties", "Destroy objects", "Compare objects", "Copy objects"],
            "correct_answer": "Initialize object properties"
        },
        {
            "question": "What does API stand for?",
            "options": ["Application Programming Interface", "Advanced Programming Integration", "Automated Process Interaction", "Application Process Interface"],
            "correct_answer": "Application Programming Interface"
        },
        {
            "question": "What is the difference between '==' and '===' in JavaScript?",
            "options": ["=== checks type and value, == only value", "Both are same", "=== is faster", "== is deprecated"],
            "correct_answer": "=== checks type and value, == only value"
        },
        {
            "question": "What is a null pointer exception?",
            "options": ["Accessing a null object reference", "Division by zero", "Array out of bounds", "Stack overflow"],
            "correct_answer": "Accessing a null object reference"
        }
    ],
    
    "Machine Learning": [
        {
            "question": "What is supervised learning?",
            "options": ["Learning with labeled data", "Learning without labels", "Reinforcement learning", "Unsupervised clustering"],
            "correct_answer": "Learning with labeled data"
        },
        {
            "question": "What is overfitting?",
            "options": ["Model performs well on training but poor on test data", "Model performs poorly on all data", "Model is too simple", "Model has no parameters"],
            "correct_answer": "Model performs well on training but poor on test data"
        },
        {
            "question": "What is the purpose of a validation set?",
            "options": ["Tune hyperparameters", "Train the model", "Final testing", "Data preprocessing"],
            "correct_answer": "Tune hyperparameters"
        },
        {
            "question": "What activation function is commonly used in hidden layers of neural networks?",
            "options": ["ReLU", "Sigmoid", "Linear", "Step function"],
            "correct_answer": "ReLU"
        },
        {
            "question": "What is gradient descent?",
            "options": ["Optimization algorithm to minimize loss", "Classification algorithm", "Data preprocessing method", "Evaluation metric"],
            "correct_answer": "Optimization algorithm to minimize loss"
        },
        {
            "question": "What is the curse of dimensionality?",
            "options": ["Problems arising from high-dimensional data", "Lack of training data", "Model complexity", "Computational cost"],
            "correct_answer": "Problems arising from high-dimensional data"
        },
        {
            "question": "What is cross-validation used for?",
            "options": ["Assess model performance reliably", "Increase training data", "Speed up training", "Reduce features"],
            "correct_answer": "Assess model performance reliably"
        }
    ],
    
    "Biology": [
        {
            "question": "What is the powerhouse of the cell?",
            "options": ["Mitochondria", "Nucleus", "Ribosome", "Golgi apparatus"],
            "correct_answer": "Mitochondria"
        },
        {
            "question": "What is the basic unit of heredity?",
            "options": ["Gene", "Cell", "Chromosome", "DNA"],
            "correct_answer": "Gene"
        },
        {
            "question": "What process do plants use to make food?",
            "options": ["Photosynthesis", "Respiration", "Digestion", "Fermentation"],
            "correct_answer": "Photosynthesis"
        },
        {
            "question": "How many chambers does the human heart have?",
            "options": ["4", "2", "3", "5"],
            "correct_answer": "4"
        },
        {
            "question": "What is DNA stand for?",
            "options": ["Deoxyribonucleic Acid", "Dynamic Nuclear Acid", "Deoxy Nitrogen Acid", "Digital Nucleic Acid"],
            "correct_answer": "Deoxyribonucleic Acid"
        },
        {
            "question": "What type of blood cells fight infection?",
            "options": ["White blood cells", "Red blood cells", "Platelets", "Plasma"],
            "correct_answer": "White blood cells"
        },
        {
            "question": "What is the largest organ in the human body?",
            "options": ["Skin", "Liver", "Brain", "Heart"],
            "correct_answer": "Skin"
        }
    ],
    
    "Computer Science": [
        {
            "question": "What does CPU stand for?",
            "options": ["Central Processing Unit", "Computer Processing Unit", "Central Program Utility", "Core Processing Unit"],
            "correct_answer": "Central Processing Unit"
        },
        {
            "question": "What is binary code?",
            "options": ["Code using 0 and 1", "Code using 0-9", "Machine language", "Assembly code"],
            "correct_answer": "Code using 0 and 1"
        },
        {
            "question": "What is an operating system?",
            "options": ["Software that manages hardware and software resources", "Application software", "Programming language", "Database system"],
            "correct_answer": "Software that manages hardware and software resources"
        },
        {
            "question": "What does RAM stand for?",
            "options": ["Random Access Memory", "Read Access Memory", "Rapid Application Memory", "Remote Access Module"],
            "correct_answer": "Random Access Memory"
        },
        {
            "question": "What is a compiler?",
            "options": ["Translates high-level code to machine code", "Executes code line by line", "Debugs code", "Optimizes code"],
            "correct_answer": "Translates high-level code to machine code"
        },
        {
            "question": "What is the purpose of cache memory?",
            "options": ["Speed up data access", "Permanent storage", "Backup data", "Input/output operations"],
            "correct_answer": "Speed up data access"
        },
        {
            "question": "What is a software bug?",
            "options": ["An error in code", "A virus", "A feature", "A hardware problem"],
            "correct_answer": "An error in code"
        }
    ]
}


def get_fallback_questions(subject: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Get fallback questions for a subject.
    
    Args:
        subject: The subject name
        num_questions: Number of questions to return (default: 5)
        
    Returns:
        List of question dictionaries with question, options, and correct_answer
    """
    # Normalize subject name for matching
    subject_normalized = subject.strip()
    
    # Try exact match first
    if subject_normalized in FALLBACK_QUESTIONS:
        questions = FALLBACK_QUESTIONS[subject_normalized]
    else:
        # Try case-insensitive partial match
        matched_key = None
        subject_lower = subject_normalized.lower()
        
        for key in FALLBACK_QUESTIONS.keys():
            if subject_lower in key.lower() or key.lower() in subject_lower:
                matched_key = key
                break
        
        if matched_key:
            questions = FALLBACK_QUESTIONS[matched_key]
        else:
            # Default to a generic subject if no match found
            # Use Programming as default since it's fairly general
            questions = FALLBACK_QUESTIONS["Programming"]
    
    # Randomly select questions if we have more than needed
    if len(questions) > num_questions:
        selected = random.sample(questions, num_questions)
    else:
        # If we need more questions than available, cycle through them
        selected = questions[:num_questions]
        while len(selected) < num_questions:
            selected.extend(questions[:num_questions - len(selected)])
    
    return selected
