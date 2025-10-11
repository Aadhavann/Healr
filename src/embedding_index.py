"""
Embedding index module for creating and searching code embeddings using ChromaDB.
"""

import os
import json
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class EmbeddingIndex:
    """Manages code embeddings and semantic search using ChromaDB."""

    def __init__(self, config_path: str = "config/settings.json", db_path: str = "chroma_db"):
        """
        Initialize the embedding index.

        Args:
            config_path: Path to configuration file
            db_path: Path to ChromaDB storage directory
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.chunk_size = config['embedding']['chunk_size']
        self.chunk_overlap = config['embedding']['chunk_overlap']
        model_name = config['embedding']['model']

        # Initialize embedding model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="code_embeddings",
            metadata={"description": "Code file embeddings for semantic search"}
        )

    def chunk_code(self, content: str, file_path: str) -> List[Dict[str, str]]:
        """
        Split code into overlapping chunks for embedding.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of chunks with metadata
        """
        lines = content.split('\n')
        chunks = []
        chunk_id = 0

        i = 0
        while i < len(lines):
            # Calculate chunk end
            chunk_end = min(i + self.chunk_size, len(lines))
            chunk_lines = lines[i:chunk_end]
            chunk_text = '\n'.join(chunk_lines)

            chunks.append({
                'id': f"{file_path}:chunk_{chunk_id}",
                'text': chunk_text,
                'file_path': file_path,
                'start_line': i + 1,
                'end_line': chunk_end,
                'chunk_id': chunk_id
            })

            chunk_id += 1
            # Move forward with overlap
            i += self.chunk_size - self.chunk_overlap

        return chunks

    def add_file(self, file_path: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a file to the embedding index.

        Args:
            file_path: Path to the file
            content: File content
            metadata: Optional metadata to store with the file
        """
        # Create chunks
        chunks = self.chunk_code(content, file_path)

        if not chunks:
            return

        # Prepare data for ChromaDB
        ids = [chunk['id'] for chunk in chunks]
        documents = [chunk['text'] for chunk in chunks]

        # Create embeddings
        embeddings = self.model.encode(documents, convert_to_numpy=True).tolist()

        # Prepare metadata
        metadatas = []
        for chunk in chunks:
            chunk_metadata = {
                'file_path': chunk['file_path'],
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line'],
                'chunk_id': chunk['chunk_id']
            }
            if metadata:
                chunk_metadata.update(metadata)
            metadatas.append(chunk_metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def add_files(self, files_data: List[Dict[str, str]]) -> None:
        """
        Add multiple files to the embedding index.

        Args:
            files_data: List of file data dictionaries from RepoParser
        """
        print(f"Adding {len(files_data)} files to embedding index...")

        for i, file_data in enumerate(files_data):
            try:
                metadata = {
                    'extension': file_data['extension'],
                    'size_kb': file_data['size_kb']
                }
                self.add_file(file_data['path'], file_data['content'], metadata)

                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(files_data)} files")

            except Exception as e:
                print(f"Error adding file {file_data['path']}: {str(e)}")

        print(f"Finished adding files to index")

    def search(self, query: str, n_results: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for relevant code chunks based on a query.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            List of relevant chunks with metadata
        """
        # Create query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True).tolist()[0]

        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )

        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

        return formatted_results

    def search_by_file(self, file_path: str, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search within a specific file.

        Args:
            file_path: Path to the file
            query: Search query
            n_results: Number of results to return

        Returns:
            List of relevant chunks from the specified file
        """
        return self.search(query, n_results, filter_dict={'file_path': file_path})

    def get_file_context(self, file_path: str, line_number: int, context_lines: int = 50) -> str:
        """
        Get code context around a specific line in a file.

        Args:
            file_path: Path to the file
            line_number: Line number to get context for
            context_lines: Number of lines of context

        Returns:
            Code context as string
        """
        # Query for chunks containing the line
        results = self.collection.get(
            where={
                'file_path': file_path
            }
        )

        if not results['ids']:
            return ""

        # Find relevant chunks
        relevant_chunks = []
        for i, metadata in enumerate(results['metadatas']):
            start = metadata['start_line']
            end = metadata['end_line']

            if start <= line_number <= end:
                relevant_chunks.append({
                    'text': results['documents'][i],
                    'start_line': start,
                    'end_line': end
                })

        if not relevant_chunks:
            return ""

        # Sort by start line and combine
        relevant_chunks.sort(key=lambda x: x['start_line'])
        return '\n'.join(chunk['text'] for chunk in relevant_chunks)

    def delete_file(self, file_path: str) -> None:
        """
        Delete all chunks of a file from the index.

        Args:
            file_path: Path to the file to delete
        """
        # Get all chunk IDs for the file
        results = self.collection.get(where={'file_path': file_path})

        if results['ids']:
            self.collection.delete(ids=results['ids'])

    def update_file(self, file_path: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Update a file in the index (delete old chunks and add new ones).

        Args:
            file_path: Path to the file
            content: New file content
            metadata: Optional metadata
        """
        self.delete_file(file_path)
        self.add_file(file_path, content, metadata)

    def get_statistics(self) -> Dict:
        """
        Get statistics about the embedding index.

        Returns:
            Dictionary containing index statistics
        """
        count = self.collection.count()

        return {
            'total_chunks': count,
            'collection_name': self.collection.name,
            'model': self.model.get_sentence_embedding_dimension()
        }

    def clear(self) -> None:
        """Clear all embeddings from the index."""
        self.client.delete_collection(name="code_embeddings")
        self.collection = self.client.create_collection(
            name="code_embeddings",
            metadata={"description": "Code file embeddings for semantic search"}
        )


if __name__ == "__main__":
    # Example usage
    index = EmbeddingIndex()

    # Add a sample file
    sample_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    result = calculate_fibonacci(10)
    print(f"Result: {result}")
"""

    index.add_file("example.py", sample_code, metadata={'extension': '.py'})

    # Search
    results = index.search("fibonacci calculation", n_results=2)
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result['id']}: {result['text'][:50]}...")
