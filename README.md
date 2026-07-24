# 🌙 DreamAssist  
## AI-Powered Adaptive Learning & Student Productivity Assistant


  An emotionally intelligent AI learning companion that combines LLM-powered tutoring, Retrieval-Augmented Generation, adaptive study planning, and personalized productivity assistance.
</p>


## 🚀 Overview

Students today face increasing academic pressure, information overload, inconsistent motivation, and difficulty maintaining effective study habits.

**DreamAssist** is an AI-powered adaptive learning platform designed to act as a personalized academic companion. It combines large language models, retrieval systems, NLP, sentiment analysis, and intelligent planning algorithms to provide students with:

- Personalized AI tutoring
- Context-aware academic assistance
- Smart study planning
- Document-based knowledge retrieval
- Emotional well-being awareness
- Learning analytics and recommendations

Unlike traditional educational tools that only provide information, DreamAssist focuses on **adaptive guidance** by understanding the student's knowledge level, learning material, performance patterns, and emotional state.


---

# ✨ Key Features

## 🤖 AI Tutor with RAG-Based Knowledge Retrieval

DreamAssist includes an AI tutoring engine capable of answering questions from a student's own academic resources.

Students can upload:

- Lecture slides
- Textbooks
- Assignments
- Notes
- Past papers
- Code files
- Handwritten notes

The system processes these documents and provides grounded answers using Retrieval-Augmented Generation.

### RAG Pipeline

```
User Query
    |
    ↓
Query Processing & Rewriting
    |
    ↓
Hybrid Retrieval
(BM25 + Vector Search)
    |
    ↓
Reciprocal Rank Fusion (RRF)
    |
    ↓
Cross Encoder Re-ranking
    |
    ↓
LLM Response Generation
    |
    ↓
Answer + Citations + Confidence Score
```

### Implemented Techniques

- Semantic chunking
- Text embeddings
- Vector similarity search
- Hybrid retrieval
- Reciprocal Rank Fusion
- Context-aware prompting
- Citation validation
- Hallucination reduction strategies


---

# 🧠 Adaptive AI Study Planner

DreamAssist generates personalized study plans based on:

- Academic performance
- Subject difficulty
- Learning speed
- Deadlines
- Motivation level
- Emotional state

The recommendation engine predicts:

| Prediction | Output |
|---|---|
| Study Intensity | Light / Moderate / Intense |
| Learning Pace | Slow / Medium / Fast |
| Break Strategy | 25-5 / 50-10 / 90-20 |

The system uses machine learning models combined with user analytics to dynamically adjust workloads and prevent burnout.


---

# ❤️ Emotion-Aware Learning Assistant

Learning performance is strongly influenced by emotional state.

DreamAssist integrates an NLP sentiment pipeline that analyzes:

- User messages
- Interaction patterns
- Mood inputs
- Procrastination signals

The system detects emotional states and adapts responses accordingly:

Example:

```
User:
"I have exams next week and I feel completely overwhelmed."

AI:
Adjusts workload,
suggests recovery breaks,
provides motivational support,
and creates a realistic study plan.
```

---

# 📚 Intelligent Document Understanding

DreamAssist supports multimodal academic content processing.

Supported inputs:

✅ PDFs  
✅ PPT slides  
✅ Word documents  
✅ Images  
✅ Handwritten notes  
✅ Programming files  


Processing pipeline:

```
Document Upload
      |
      ↓
File Detection
      |
      ↓
OCR Extraction (if required)
      |
      ↓
Text Cleaning
      |
      ↓
AI Semantic Chunking
      |
      ↓
Embedding Generation
      |
      ↓
Vector Database Storage
```

---

# 🧩 AI Persona System

DreamAssist provides interactive AI personalities to improve engagement.

Examples:

- Einstein-inspired analytical tutor
- Curie-inspired supportive mentor
- Newton-inspired problem-solving assistant


Each persona maintains:

- Consistent communication style
- Personalized teaching approach
- Domain-specific behavior


---

# 🏗️ System Architecture

```
                    Mobile Application
                           |
                           |
                    FastAPI Backend
                           |
        -------------------------------------
        |                 |                 |
        ↓                 ↓                 ↓

   User System       AI Services       Analytics

                         |
        -------------------------------------
        |
        ↓

              AI Orchestration Layer

        -------------------------------------
        |                 |                 |

       RAG            Sentiment        Planner
     Pipeline         Analysis        Engine

        |
        ↓

 Vector Database + LLM APIs + ML Models

```


---

# 🛠️ Technology Stack

## Artificial Intelligence

- Large Language Models
- Retrieval-Augmented Generation (RAG)
- Prompt Engineering
- NLP
- Sentiment Analysis
- Embeddings
- AI Agents


## Machine Learning

- Scikit-learn
- Decision Tree Classifiers
- DistilBERT
- Model Evaluation


## Backend

- Python
- FastAPI
- REST APIs


## AI Frameworks

- LangChain
- Groq LLM
- AWS Bedrock


## Databases

- ChromaDB
- Vector Search
- SQLite


## Deployment

- Docker
- Containerized AI services


---

# 🔬 Technical Highlights

## 1. Hybrid Retrieval with Reciprocal Rank Fusion

To improve retrieval quality, DreamAssist combines:

- BM25 lexical search
- Dense vector similarity search

The rankings are merged using:

```
RRF Score = Σ 1/(rank + k)
```

This improves both:

- Keyword precision
- Semantic understanding


---

## 2. AI-Based Semantic Chunking

Instead of fixed-size splitting, documents are intelligently divided based on meaning.

Examples:

- Slides → slide-level chunks
- Code → function-level chunks
- Books → section-level chunks


Benefits:

- Better context preservation
- Higher retrieval accuracy
- Reduced hallucinations


---

## 3. Context-Aware Prompt Engineering

The tutoring engine dynamically modifies prompts using:

- User proficiency
- Learning history
- Emotional signals
- Retrieved academic context


Example:

```
Beginner student:
Explain concepts step-by-step with examples.

Advanced student:
Provide deeper reasoning and technical details.
```


---

## 4. App Walkthrough

<img width="1126" height="601" alt="image" src="https://github.com/user-attachments/assets/4c3dfc87-3d8c-448b-b472-a367af210080" />
<img width="478" height="752" alt="image" src="https://github.com/user-attachments/assets/ed0c185f-6c9e-4b77-9b82-e33565ade685" />
<img width="1135" height="596" alt="image" src="https://github.com/user-attachments/assets/552111d3-dc28-42ec-a3e2-c12b97cf72f9" />
<img width="1317" height="697" alt="image" src="https://github.com/user-attachments/assets/a3f6e570-5769-49b8-b108-1ea198f9a3a7" />


# 📊 Future Improvements

Planned enhancements:

- Reinforcement learning for personalized teaching strategies
- Voice-based AI tutor
- Real-time lecture assistant
- Knowledge graph generation
- Multi-agent AI architecture
- Long-term memory system
- Advanced evaluation framework for RAG quality


---

# 👩‍💻 Author

**Rameen Jamshed**

Artificial Intelligence Engineer

Bachelor of Artificial Intelligence  
COMSATS University Islamabad



---

# 📄 License

This project was developed as a Bachelor's Final Year Project and is intended for educational and research purposes.
