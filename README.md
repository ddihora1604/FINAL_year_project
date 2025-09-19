# RAG Pipeline for Customer Support

This project implements a Retrieval-Augmented Generation (RAG) pipeline for customer support using the provided CSV dataset.

## Overview

The RAG pipeline performs the following steps:
1. **Data Loading**: Loads and preprocesses the customer support CSV data
2. **Embedding Generation**: Creates vector embeddings using sentence transformers
3. **Vector Store**: Builds a FAISS index for efficient similarity search
4. **Query Processing**: Enables semantic search to find relevant support responses

## Features

- **Semantic Search**: Find relevant customer support responses using natural language queries
- **Vector Similarity**: Uses sentence transformers for high-quality embeddings
- **Efficient Retrieval**: FAISS-based vector store for fast similarity search
- **Flexible Architecture**: Easy to extend and modify for different datasets
- **Persistence**: Save and load trained models for reuse

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your CSV file is in the RAG-Pipeline directory

## Usage

### Basic Usage

```python
from rag_pipeline import RAGPipeline

# Initialize pipeline
rag = RAGPipeline()

# Load and process data
rag.load_and_process_data('customer_support_sample_1500_balanced.csv')
rag.generate_embeddings()
rag.build_vector_store()

# Search for relevant documents
results = rag.search("How do I reset my password?", top_k=5)
```

### Interactive Demo

Run the example script for an interactive demo:

```bash
cd RAG-Pipeline
python example_usage.py
```

## File Structure

```
RAG-Pipeline/
├── rag_pipeline.py              # Main RAG pipeline implementation
├── example_usage.py             # Interactive demo script
├── customer_support_sample_1500_balanced.csv  # Dataset
└── saved_pipeline/              # Saved model artifacts (created after first run)
    ├── embeddings.npy
    ├── faiss_index.bin
    ├── documents.pkl
    └── metadata.pkl
```

## Technical Details

### Components

1. **RAGPipeline Class**: Main class that orchestrates the entire pipeline
2. **Text Preprocessing**: Cleans and normalizes text data
3. **Embedding Model**: Uses `all-MiniLM-L6-v2` sentence transformer
4. **Vector Store**: FAISS IndexFlatIP for cosine similarity search
5. **Search Interface**: Semantic search with configurable top-k results

### Model Details

- **Embedding Model**: `all-MiniLM-L6-v2` (384-dimensional vectors)
- **Similarity Metric**: Cosine similarity
- **Index Type**: FAISS Flat Inner Product
- **Text Processing**: Lowercasing, whitespace normalization, special character removal

## Performance

The pipeline is optimized for:
- **Fast Retrieval**: Sub-second query response times
- **Memory Efficiency**: Optimized embedding storage
- **Scalability**: Can handle datasets with thousands of documents
- **Accuracy**: High-quality semantic matching

## Customization

### Using Different Models

```python
# Use a different sentence transformer model
rag = RAGPipeline(model_name='paraphrase-MiniLM-L12-v2')
```

### Adjusting Search Parameters

```python
# Get more or fewer results
results = rag.search("query", top_k=10)
```

### Custom Preprocessing

Modify the `preprocess_text` method in `RAGPipeline` class for custom text processing.

## Dependencies

- pandas: Data manipulation
- numpy: Numerical operations
- sentence-transformers: Text embedding generation
- faiss-cpu: Vector similarity search
- scikit-learn: Additional ML utilities
- torch: PyTorch backend for transformers

## Future Enhancements

- [ ] Add support for different embedding models
- [ ] Implement query expansion techniques
- [ ] Add evaluation metrics
- [ ] Support for multiple languages
- [ ] Integration with generative models for complete RAG