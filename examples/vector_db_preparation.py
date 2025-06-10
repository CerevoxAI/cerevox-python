#!/usr/bin/env python3
"""
Vector Database Preparation Example using Cerevox Document Loader

This comprehensive example demonstrates all the advanced document chunking and vector database
preparation features available in the Cerevox document_loader module.

🚀 FEATURES DEMONSTRATED:

🧩 ELEMENT-LEVEL CHUNKING:
• get_chunked_elements() - Element-level chunking with rich metadata
• Format-aware chunking (text, markdown, html)
• Element type distribution tracking
• Traceable chunk-to-element mapping

📄 DOCUMENT-LEVEL CHUNKING:
• get_text_chunks() - Smart plain text chunking with size control
• get_markdown_chunks() - Markdown-aware chunking preserving formatting
• Precise size control with configurable tolerance (percentage-based)
• Smart boundary detection (paragraphs, sentences, words)

📦 BATCH-LEVEL OPERATIONS:
• get_all_text_chunks() - Batch text chunking with optional metadata
• get_all_markdown_chunks() - Batch markdown chunking with metadata
• get_combined_chunks() - Combined document chunking strategies
• Efficient multi-document processing with batch statistics

🛠️ STANDALONE FUNCTIONS:
• chunk_text() - Direct text chunking for any content
• chunk_markdown() - Direct markdown chunking with format preservation
• Advanced boundary preservation and tolerance handling

🔍 SEARCH & FILTERING:
• search_content() - Advanced content search within documents
• search_all() - Batch-wide content search across multiple documents
• get_elements_by_page() - Page-specific element retrieval
• get_elements_by_type() - Element type filtering
• filter_by_type() - Document filtering by file type
• filter_by_page_count() - Document filtering by page count
• get_documents_by_element_type() - Filter documents containing specific elements

📊 CONTENT ANALYSIS & STATISTICS:
• get_statistics() - Comprehensive document analysis
• get_content_similarity_matrix() - Document similarity analysis
• extract_key_phrases() - Key phrase extraction for enhanced indexing
• get_reading_time() - Content length estimation
• get_language_info() - Basic language detection

📋 EXPORT & PREPROCESSING:
• to_dict() - Structured data export for custom processing
• to_markdown() - Enhanced markdown with metadata
• to_html() - Rich HTML export with styling
• to_pandas_tables() - Table extraction for structured data indexing
• export_tables_to_csv() - Batch table export

🗄️ VECTOR DATABASE INTEGRATION:
• Pinecone integration patterns with optimal chunk sizing
• Weaviate integration with rich document structure
• ChromaDB batch processing with metadata filtering
• Qdrant integration with advanced payload structure
• Production-ready patterns for major vector databases

🛡️ VALIDATION & ERROR HANDLING:
• validate() - Document structure validation
• Robust error handling for malformed content
• Graceful degradation for missing dependencies

🎯 ADVANCED FEATURES:
• Precise size control with configurable tolerance (percentage-based)
• Smart boundary detection (paragraphs, sentences, words)
• Code block preservation in markdown
• Rich metadata inclusion for enhanced retrieval
• Multiple format support (text, markdown, html)
• Element-type awareness for specialized chunking
• Table structure preservation and extraction
• Batch processing with deduplication patterns

💎 COMPETITIVE ADVANTAGES:
• Semantic-aware chunking respecting document structure
• Vector database optimization out-of-the-box
• Advanced element metadata for enhanced search
• Built-in integration patterns for popular vector DBs
• Production-ready performance optimization
• Unmatched accuracy in document structure preservation
• Comprehensive content analysis and preprocessing tools

"""

import textwrap

from cerevox.document_loader import (
    Document,
    DocumentBatch,
    DocumentMetadata,
    chunk_markdown,
    chunk_text,
)

# For demonstration purposes - sample document data
SAMPLE_DOCUMENT_DATA = {
    "filename": "sample_report.pdf",
    "content": textwrap.dedent(
        """
        # Annual Financial Report 2024

        ## Executive Summary

        This comprehensive annual report presents our financial performance for the fiscal year 2024. Our organization has demonstrated remarkable growth across all key performance indicators, with revenue increasing by 23% compared to the previous year.

        ### Key Highlights

        - **Revenue Growth**: $45.2M (+23% YoY)
        - **Profit Margin**: 18.5% (+2.1% YoY) 
        - **Customer Satisfaction**: 94.2% (+3.8% YoY)
        - **Employee Retention**: 91.7% (+5.2% YoY)

        ## Financial Performance

        ### Revenue Analysis

        Our revenue streams showed consistent growth across all divisions:

        1. **Software Solutions**: $28.3M (+31% YoY)
        2. **Consulting Services**: $12.8M (+18% YoY)
        3. **Support & Maintenance**: $4.1M (+8% YoY)

        The software solutions division continues to be our primary growth driver, with new AI-powered features driving increased customer adoption.

        ### Cost Management

        ```python
        # Cost optimization model
        def calculate_cost_efficiency(revenue, expenses):
            efficiency_ratio = (revenue - expenses) / revenue
            return {
                "efficiency": efficiency_ratio,
                "profit_margin": efficiency_ratio * 100,
                "recommendation": "optimize" if efficiency_ratio < 0.15 else "maintain"
            }

        # Example calculation
        result = calculate_cost_efficiency(45200000, 36800000)
        print(f"Profit margin: {result['profit_margin']:.1f}%")
        ```

        ## Market Analysis

        The technology sector experienced significant volatility in 2024, with AI and machine learning companies leading growth. Our strategic positioning in this space has enabled us to capitalize on emerging opportunities.

        ### Competitive Landscape

        | Competitor | Market Share | Growth Rate |
        |------------|--------------|-------------|
        | Company A  | 32.1%        | +15.2%      |
        | Company B  | 28.7%        | +12.8%      |
        | Our Company| 24.3%        | +23.0%      |
        | Company C  | 15.9%        | +8.1%       |

        ## Future Outlook

        Looking ahead to 2025, we anticipate continued growth driven by:

        - Expansion into European markets
        - Launch of next-generation AI platform
        - Strategic partnerships with leading technology companies
        - Investment in research and development

        ## Conclusion

        The 2024 fiscal year has been exceptional for our company. With strong financial performance, strategic market positioning, and a clear roadmap for growth, we are well-positioned for continued success in 2025 and beyond.

        Our commitment to innovation, customer satisfaction, and operational excellence remains unwavering as we navigate the evolving technology landscape.
        """
    ).strip(),
    "file_type": "pdf",
    "total_pages": 15,
    "total_elements": 42,
}


def demonstrate_document_chunking():
    """
    Demonstrate document-level chunking methods.
    """

    print("\n🚀 Document-Level Chunking Methods")
    print("=" * 60)
    print("💡 Use these methods to chunk documents for vector databases")
    print("📌 Perfect for preprocessing content before Document creation")

    # Sample content with various markdown elements
    sample_markdown = textwrap.dedent(
        """# Research Report: AI in Healthcare

        ## Executive Summary

        This quarterly report analyzes AI adoption trends in healthcare and provides strategic recommendations for healthcare organizations. The analysis covers multiple sectors including diagnostics, treatment planning, and patient care optimization.

        ## Key Findings

        ### Diagnostic AI Applications

        The healthcare AI sector showed remarkable growth with a 34% increase in diagnostic tool adoption. Key drivers include:

        - **Medical Imaging**: 67% improvement in accuracy
        - **Pathology Analysis**: 45% faster diagnosis  
        - **Radiology Screening**: 29% reduction in false positives

        ### Treatment Optimization

        AI-powered treatment planning has revolutionized patient care:

        1. Personalized treatment protocols increased by 52%
        2. Drug discovery timelines shortened by 38%
        3. Clinical trial efficiency improved by 41%

        ### Implementation Challenges

        ```python
        # AI Implementation Scoring Model
        def calculate_ai_readiness(data_quality, staff_training, infrastructure):
            weights = {"data": 0.4, "training": 0.3, "infrastructure": 0.3}
            
            score = (
                data_quality * weights["data"] + 
                staff_training * weights["training"] + 
                infrastructure * weights["infrastructure"]
            )
            
            if score >= 0.8:
                return "Ready for full AI deployment"
            elif score >= 0.6:
                return "Requires targeted improvements"
            else:
                return "Needs comprehensive preparation"

        # Example assessment
        readiness = calculate_ai_readiness(0.85, 0.70, 0.75)
        print(f"AI Readiness: {readiness}")
        ```

        ## Market Analysis

        | Healthcare Sector | AI Adoption | ROI Improvement |
        |------------------|-------------|-----------------|
        | Radiology        | 78%         | +45%            |
        | Pathology        | 65%         | +38%            |
        | Emergency Care   | 52%         | +22%            |
        | Primary Care     | 34%         | +15%            |

        ## Recommendations

        Based on our analysis, we recommend the following strategic priorities:

        ### Short-term (6 months)
        - Implement AI-powered diagnostic tools in radiology
        - Train medical staff on AI system integration
        - Establish data quality standards

        ### Medium-term (12 months)  
        - Expand AI adoption to pathology departments
        - Develop AI governance frameworks
        - Create patient data privacy protocols

        ### Long-term (24 months)
        - Full AI integration across all departments
        - Advanced predictive analytics for patient outcomes
        - AI-driven research and development initiatives

        ## Conclusion

        The healthcare AI market presents unprecedented opportunities for organizations ready to embrace technological transformation. Success requires strategic planning, staff development, and robust data infrastructure.
        """
    ).strip()

    # Demonstrate different chunking strategies
    test_configs = [
        {"size": 300, "tolerance": 0.1, "purpose": "Embedding Generation"},
        {"size": 500, "tolerance": 0.15, "purpose": "Vector Search Optimization"},
        {"size": 800, "tolerance": 0.2, "purpose": "Context Window Utilization"},
        {"size": 1000, "tolerance": 0.1, "purpose": "Document Summarization"},
    ]

    print(f"\n📄 Sample Content: {len(sample_markdown)} characters")
    print(
        "📋 Content includes: headers, lists, code blocks, tables, and structured text"
    )

    for config in test_configs:
        target_size = config["size"]
        tolerance = config["tolerance"]
        purpose = config["purpose"]

        print(f"\n📏 Chunking Strategy: {purpose}")
        print(f"🎯 Target size: {target_size} chars, Tolerance: {tolerance*100}%")
        print("-" * 50)

        # Text chunking (removes formatting)
        text_chunks = chunk_text(
            sample_markdown, target_size=target_size, tolerance=tolerance
        )
        text_sizes = [len(chunk) for chunk in text_chunks]

        print(f"🔤 Text Chunking:")
        print(f"   Chunks generated: {len(text_chunks)}")
        print(f"   Size range: {min(text_sizes)}-{max(text_sizes)} chars")
        print(f"   Average size: {sum(text_sizes)/len(text_sizes):.0f} chars")

        # Markdown chunking (preserves formatting)
        md_chunks = chunk_markdown(
            sample_markdown, target_size=target_size, tolerance=tolerance
        )
        md_sizes = [len(chunk) for chunk in md_chunks]

        print(f"📝 Markdown Chunking:")
        print(f"   Chunks generated: {len(md_chunks)}")
        print(f"   Size range: {min(md_sizes)}-{max(md_sizes)} chars")
        print(f"   Average size: {sum(md_sizes)/len(md_sizes):.0f} chars")

        # Show how code blocks are preserved in markdown chunking
        code_chunks = [i for i, chunk in enumerate(md_chunks) if "```" in chunk]
        if code_chunks:
            print(f"💻 Code blocks preserved in chunks: {code_chunks}")

        # Show structure preservation
        header_chunks = [
            i for i, chunk in enumerate(md_chunks) if chunk.strip().startswith("#")
        ]
        if header_chunks:
            print(f"📑 Chunks starting with headers: {header_chunks}")

    # Demonstrate chunk content preview
    print(f"\n👀 Chunk Content Examples (Target: 500 chars)")
    print("-" * 50)

    demo_chunks = chunk_markdown(sample_markdown, target_size=500, tolerance=0.15)

    for i, chunk in enumerate(demo_chunks[:3]):  # Show first 3 chunks
        preview_lines = chunk.split("\n")[:3]  # First 3 lines
        print(f"\n📋 Chunk {i+1} ({len(chunk)} chars):")
        for line in preview_lines:
            print(f"   {line}")
        if len(chunk.split("\n")) > 3:
            print("   ...")

    # Show advanced features
    print(f"\n✨ Advanced Chunking Features:")
    print("🧠 Smart boundary detection (respects paragraphs, sentences)")
    print("📊 Configurable tolerance for size optimization")
    print("🔒 Code block integrity preservation")
    print("📋 Table structure maintenance")
    print("🎯 Header hierarchy awareness")
    print("🔄 Semantic boundary prioritization")

    return demo_chunks


def demonstrate_element_chunking():
    """
    Demonstrate element-level chunking with rich metadata.
    """

    print("\n🧩 Element-Level Chunking Methods")
    print("=" * 60)
    print("💡 Use these methods to chunk document elements with rich metadata")
    print("📌 Perfect for advanced vector database preparation with element context")

    # Create a sample document with elements
    sample_doc = Document(
        content=SAMPLE_DOCUMENT_DATA["content"],
        metadata=DocumentMetadata(
            filename="annual_report.pdf",
            file_type="pdf",
            total_pages=15,
            total_elements=42,
        ),
    )

    # Demonstrate get_chunked_elements with different formats
    print(f"\n📋 Document: {sample_doc.filename}")
    print(f"📄 Content length: {len(sample_doc.content)} characters")
    print(f"🔢 Total elements: {len(sample_doc.elements)}")

    # Test different formats
    formats = ["text", "markdown", "html"]

    for format_type in formats:
        print(f"\n🎯 Element Chunking Format: {format_type.upper()}")
        print("-" * 40)

        try:
            chunked_elements = sample_doc.get_chunked_elements(
                target_size=400, tolerance=0.15, format_type=format_type
            )

            print(f"✅ Generated {len(chunked_elements)} element chunks")

            if chunked_elements:
                # Show sample chunk metadata
                sample_chunk = chunked_elements[0]
                print(f"\n📋 Sample chunk metadata:")
                print(f"   Content length: {len(sample_chunk['content'])}")
                print(f"   Element ID: {sample_chunk['element_id']}")
                print(f"   Element type: {sample_chunk['element_type']}")
                print(f"   Page number: {sample_chunk['page_number']}")
                print(f"   Chunk index: {sample_chunk['chunk_index']}")
                print(f"   Total chunks for element: {sample_chunk['total_chunks']}")
                print(f"   Format type: {sample_chunk['format_type']}")

                # Show element type distribution
                element_types = {}
                for chunk in chunked_elements:
                    elem_type = chunk["element_type"]
                    element_types[elem_type] = element_types.get(elem_type, 0) + 1

                print(f"\n📊 Element type distribution:")
                for elem_type, count in element_types.items():
                    print(f"   {elem_type}: {count} chunks")

        except Exception as e:
            print(f"❌ Error with {format_type} format: {e}")

    print(f"\n✨ Element Chunking Benefits:")
    print("🔍 Rich metadata for enhanced search")
    print("📄 Element-level context preservation")
    print("🎯 Format-aware chunking (text/markdown/html)")
    print("📊 Element type distribution tracking")
    print("🔗 Traceable chunk-to-element mapping")

    return chunked_elements if "chunked_elements" in locals() else []


def demonstrate_batch_operations():
    """
    Demonstrate batch-level operations for multiple documents.
    """

    print("\n📦 Batch-Level Operations")
    print("=" * 60)
    print("💡 Use these operations to handle multiple documents efficiently")
    print("📌 Perfect for vector database preparation and batch processing")

    # Create sample documents for batch processing
    sample_docs = []
    for i in range(3):
        doc_content = (
            SAMPLE_DOCUMENT_DATA["content"] + f"\n\nDocument {i+1} specific content."
        )
        doc = Document(
            content=doc_content,
            metadata=DocumentMetadata(
                filename=f"document_{i+1}.pdf",
                file_type="pdf",
                total_pages=5 + i,
                total_elements=20 + i * 5,
            ),
        )
        sample_docs.append(doc)

    # Create DocumentBatch
    batch = DocumentBatch(sample_docs)

    print(f"\n📊 Batch Info: {len(batch)} documents")
    print(f"📄 Total pages: {batch.total_pages}")
    print(f"📝 Total content length: {batch.total_content_length:,} characters")

    # Method 1: Get all text chunks with metadata
    print("\n🔄 Method 1: Get all text chunks with metadata")
    print("-" * 50)

    all_text_chunks = batch.get_all_text_chunks(target_size=500, include_metadata=True)
    print(f"✅ Generated {len(all_text_chunks)} text chunks with metadata")

    # Show metadata structure
    if all_text_chunks:
        sample_chunk = all_text_chunks[0]
        print(f"\n📋 Sample chunk metadata:")
        print(f"   Content length: {len(sample_chunk['content'])}")
        print(f"   Source file: {sample_chunk['metadata']['filename']}")
        print(f"   Chunk index: {sample_chunk['metadata']['chunk_index']}")
        print(
            f"   Total chunks from this doc: {sample_chunk['metadata']['total_chunks']}"
        )
        print(
            f"   Document index in batch: {sample_chunk['metadata']['document_index']}"
        )

    # Method 2: Get all markdown chunks with metadata
    print("\n📝 Method 2: Get all markdown chunks with metadata")
    print("-" * 50)

    all_markdown_chunks = batch.get_all_markdown_chunks(
        target_size=700, include_metadata=True
    )
    print(f"✅ Generated {len(all_markdown_chunks)} markdown chunks with metadata")

    # Show metadata structure
    if all_markdown_chunks:
        sample_chunk = all_markdown_chunks[0]
        print(f"\n📋 Sample chunk metadata:")
        print(f"   Content length: {len(sample_chunk['content'])}")
        print(f"   Source file: {sample_chunk['metadata']['filename']}")
        print(f"   Chunk index: {sample_chunk['metadata']['chunk_index']}")
        print(f"   Document index: {sample_chunk['metadata']['document_index']}")

    # Method 3: Get combined chunks (different strategies)
    print("\n🔗 Method 3: Get combined chunks")
    print("-" * 50)

    # Text format
    combined_text_chunks = batch.get_combined_chunks(
        target_size=600, format_type="text"
    )
    print(f"✅ Combined text chunks: {len(combined_text_chunks)}")

    # Markdown format
    combined_md_chunks = batch.get_combined_chunks(
        target_size=600, format_type="markdown"
    )
    print(f"✅ Combined markdown chunks: {len(combined_md_chunks)}")

    # Method 4: Get chunks without metadata (simple format)
    print("\n📄 Method 4: Get chunks without metadata")
    print("-" * 50)

    simple_text_chunks = batch.get_all_text_chunks(
        target_size=400, include_metadata=False
    )
    simple_md_chunks = batch.get_all_markdown_chunks(
        target_size=400, include_metadata=False
    )

    print(f"✅ Simple text chunks: {len(simple_text_chunks)}")
    print(f"✅ Simple markdown chunks: {len(simple_md_chunks)}")

    # Show chunk size statistics
    print(f"\n📊 Chunk Statistics:")
    text_sizes = [len(chunk["content"]) for chunk in all_text_chunks]
    print(
        f"   Text chunks - Min: {min(text_sizes)}, Max: {max(text_sizes)}, Avg: {sum(text_sizes)/len(text_sizes):.0f}"
    )

    md_sizes = [len(chunk["content"]) for chunk in all_markdown_chunks]
    print(
        f"   Markdown chunks - Min: {min(md_sizes)}, Max: {max(md_sizes)}, Avg: {sum(md_sizes)/len(md_sizes):.0f}"
    )

    print(f"\n✨ Batch Processing Benefits:")
    print("🚀 Efficient multi-document processing")
    print("🏷️  Rich metadata for each chunk")
    print("📊 Batch-level statistics and analysis")
    print("🔄 Multiple chunking strategies in one call")
    print("📦 Consistent formatting across documents")

    return batch


def demonstrate_standalone_chunking():
    """
    Demonstrate standalone chunking functions for any text content.
    """

    print("\n🛠️  Standalone Chunking Functions")
    print("=" * 60)
    print("💡 Use these functions to chunk any text content directly")
    print("📌 Perfect for preprocessing text before creating Document objects")

    # Sample content for different use cases
    sample_texts = {
        "technical_doc": textwrap.dedent(
            """
            # Technical Implementation Guide
            
            ## Overview
            This guide covers the implementation of our new API system. The system is designed to handle high-throughput requests with minimal latency.
            
            ### Architecture Components
            - **API Gateway**: Routes requests to appropriate services
            - **Load Balancer**: Distributes traffic across instances  
            - **Database Layer**: Manages persistent data storage
            - **Cache Layer**: Provides fast data retrieval
            
            ## Setup Instructions
            1. Install dependencies using `npm install`
            2. Configure environment variables
            3. Run database migrations
            4. Start the application server
            
            ```javascript
            // Example configuration
            const config = {
                port: process.env.PORT || 3000,
                database: {
                    host: process.env.DB_HOST,
                    port: process.env.DB_PORT,
                    name: process.env.DB_NAME
                }
            };
            ```
        """
        ).strip(),
        "research_paper": textwrap.dedent(
            """
            Abstract: This study examines the impact of artificial intelligence on healthcare outcomes. We analyzed data from 1,000 hospitals over a 3-year period. Results show significant improvements in diagnostic accuracy and patient satisfaction. AI-powered tools reduced diagnostic errors by 34% and improved treatment planning efficiency by 28%. These findings suggest that AI integration in healthcare systems can substantially enhance patient care quality.
            
            Introduction: Healthcare systems worldwide face increasing pressure to improve outcomes while managing costs. Artificial intelligence presents a promising solution to these challenges. This research investigates the quantitative impact of AI implementation across multiple healthcare metrics.
            
            Methodology: We conducted a comprehensive analysis using data from hospitals that implemented AI diagnostic tools between 2021-2024. Primary metrics included diagnostic accuracy, treatment planning time, patient satisfaction scores, and clinical outcomes.
        """
        ).strip(),
        "legal_document": textwrap.dedent(
            """
            WHEREAS, the parties desire to enter into this Agreement to establish the terms and conditions governing their business relationship; and WHEREAS, each party has the requisite power and authority to enter into this Agreement; NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the parties agree as follows: 1. DEFINITIONS. For purposes of this Agreement, the following terms shall have the meanings set forth below: (a) "Confidential Information" means any non-public information disclosed by one party to the other. (b) "Effective Date" means the date this Agreement is executed by both parties. 2. OBLIGATIONS. Each party agrees to maintain the confidentiality of all Confidential Information received from the other party.
        """
        ).strip(),
    }

    # Test different chunking strategies
    strategies = [
        {"size": 200, "tolerance": 0.1, "purpose": "Small chunks for embeddings"},
        {"size": 500, "tolerance": 0.15, "purpose": "Medium chunks for search"},
        {"size": 1000, "tolerance": 0.2, "purpose": "Large chunks for context"},
    ]

    for doc_type, content in sample_texts.items():
        print(f"\n📄 Document Type: {doc_type.replace('_', ' ').title()}")
        print(f"📝 Content length: {len(content)} characters")
        print("-" * 50)

        for strategy in strategies:
            target_size = strategy["size"]
            tolerance = strategy["tolerance"]
            purpose = strategy["purpose"]

            print(f"\n🎯 Strategy: {purpose}")
            print(f"   Target size: {target_size} chars, Tolerance: {tolerance*100}%")

            # Text chunking
            text_chunks = chunk_text(
                content, target_size=target_size, tolerance=tolerance
            )
            text_sizes = [len(chunk) for chunk in text_chunks]

            print(f"   📄 Text chunks: {len(text_chunks)} chunks")
            print(f"      Size range: {min(text_sizes)}-{max(text_sizes)} chars")
            print(f"      Average: {sum(text_sizes)/len(text_sizes):.0f} chars")

            # Markdown chunking (if content has markdown)
            if "#" in content or "```" in content or "*" in content:
                md_chunks = chunk_markdown(
                    content, target_size=target_size, tolerance=tolerance
                )
                md_sizes = [len(chunk) for chunk in md_chunks]

                print(f"   📝 Markdown chunks: {len(md_chunks)} chunks")
                print(f"      Size range: {min(md_sizes)}-{max(md_sizes)} chars")
                print(f"      Average: {sum(md_sizes)/len(md_sizes):.0f} chars")

                # Check for preserved structures
                has_headers = sum(
                    1 for chunk in md_chunks if chunk.strip().startswith("#")
                )
                has_code = sum(1 for chunk in md_chunks if "```" in chunk)
                has_lists = sum(
                    1 for chunk in md_chunks if "\n-" in chunk or "\n*" in chunk
                )

                if has_headers or has_code or has_lists:
                    print(
                        f"      Preserved: headers({has_headers}), code({has_code}), lists({has_lists})"
                    )

    # Demonstrate advanced chunking features
    print(f"\n🔧 Advanced Chunking Features:")
    print("-" * 50)

    # Test boundary preservation
    test_text = "First sentence. Second sentence! Third sentence? Fourth sentence."

    print(f"\n📝 Boundary Preservation Test:")
    print(f"   Input: '{test_text}'")

    small_chunks = chunk_text(test_text, target_size=20, tolerance=0.3)
    print(f"   Small chunks ({len(small_chunks)}): {small_chunks}")

    # Test tolerance handling
    print(f"\n📏 Tolerance Handling:")
    long_text = "This is a test document. " * 50  # ~1250 chars

    for tolerance in [0.1, 0.2, 0.5]:
        chunks = chunk_text(long_text, target_size=300, tolerance=tolerance)
        sizes = [len(chunk) for chunk in chunks]
        print(
            f"   Tolerance {tolerance*100}%: {len(chunks)} chunks, sizes {min(sizes)}-{max(sizes)}"
        )

    print(f"\n✨ Standalone Function Benefits:")
    print("🚀 Direct text processing without Document objects")
    print("⚡ Fast processing for large text datasets")
    print("🎯 Precise size control with tolerance settings")
    print("🧠 Smart boundary detection (sentences, paragraphs)")
    print("📋 Format preservation (markdown structures)")
    print("🔄 Consistent chunking across different content types")

    return text_chunks if "text_chunks" in locals() else []


def demonstrate_search_and_filtering():
    """
    Demonstrate search and filtering capabilities for vector database preparation.
    """

    print("\n🔍 Search and Filtering Capabilities")
    print("=" * 60)
    print("💡 Use these methods to filter and search content before vectorization")
    print("📌 Perfect for preprocessing and content discovery")

    # Create sample documents with varied content
    sample_docs = []

    # Document 1: Technical content
    doc1_content = textwrap.dedent(
        """
        # API Documentation
        
        ## Authentication
        Our API uses OAuth 2.0 for authentication. Include your access token in the Authorization header.
        
        ## Endpoints
        
        ### GET /users
        Retrieve user information. Requires 'read:users' scope.
        
        ### POST /documents
        Upload new documents. Maximum file size is 50MB.
        
        ## Rate Limiting
        API calls are limited to 1000 requests per hour per API key.
    """
    ).strip()

    doc1 = Document(
        content=doc1_content,
        metadata=DocumentMetadata(filename="api_docs.md", file_type="markdown"),
    )

    # Document 2: Business content
    doc2_content = textwrap.dedent(
        """
        # Quarterly Business Review
        
        ## Financial Performance
        Revenue increased by 23% this quarter, reaching $2.3M in total sales.
        
        ## Customer Metrics
        - New customers: 150
        - Customer retention: 94%
        - Support tickets resolved: 1,247
        
        ## Market Analysis
        The SaaS market continues to grow, with our primary competitors showing similar growth patterns.
    """
    ).strip()

    doc2 = Document(
        content=doc2_content,
        metadata=DocumentMetadata(filename="business_review.md", file_type="markdown"),
    )

    # Document 3: Research content
    doc3_content = textwrap.dedent(
        """
        # Machine Learning Research Paper
        
        ## Abstract
        This paper presents a novel approach to natural language processing using transformer architectures.
        
        ## Introduction
        Large language models have revolutionized AI applications across multiple domains.
        
        ## Methodology
        We trained our model on a diverse dataset of 100M documents using distributed computing.
        
        ## Results
        Our approach achieved 95% accuracy on standard benchmarks, outperforming previous methods.
    """
    ).strip()

    doc3 = Document(
        content=doc3_content,
        metadata=DocumentMetadata(filename="research_paper.pdf", file_type="pdf"),
    )

    sample_docs = [doc1, doc2, doc3]
    batch = DocumentBatch(sample_docs)

    print(f"\n📊 Sample Data: {len(batch)} documents")
    print(f"📄 File types: {batch.file_types}")

    # Demonstration 1: Document-level content search
    print("\n🔍 Document-Level Content Search")
    print("-" * 50)

    search_terms = ["API", "revenue", "machine learning", "authentication"]

    for term in search_terms:
        print(f"\n🔎 Searching for: '{term}'")

        for doc in sample_docs:
            matches = doc.search_content(
                term, case_sensitive=False, include_tables=True
            )
            if matches:
                print(f"   ✅ Found in {doc.filename}: {len(matches)} elements")
                # Show a preview of the first match
                if matches[0].text:
                    preview = (
                        matches[0].text[:100] + "..."
                        if len(matches[0].text) > 100
                        else matches[0].text
                    )
                    print(f"      Preview: {preview}")
            else:
                print(f"   ❌ Not found in {doc.filename}")

    # Demonstration 2: Batch-wide search
    print("\n📦 Batch-Wide Search")
    print("-" * 50)

    batch_search_terms = ["customers", "model", "documents"]

    for term in batch_search_terms:
        print(f"\n🔎 Batch search for: '{term}'")
        results = batch.search_all(term, case_sensitive=False)

        print(f"   📊 Found in {len(results)} documents:")
        for doc, matches in results:
            print(f"      {doc.filename}: {len(matches)} matches")

    # Demonstration 3: Document filtering
    print("\n🗂️  Document Filtering")
    print("-" * 50)

    # Filter by file type
    print("📄 Filter by file type:")
    markdown_docs = batch.filter_by_type("markdown")
    pdf_docs = batch.filter_by_type("pdf")
    print(f"   Markdown documents: {len(markdown_docs)} files")
    print(f"   PDF documents: {len(pdf_docs)} files")

    # Filter by content characteristics
    print("\n📏 Filter by content characteristics:")

    # Find documents with specific keywords
    keyword_results = batch.find_documents_with_keyword("API", case_sensitive=False)
    print(f"   Documents containing 'API': {len(keyword_results)}")
    for doc, count in keyword_results:
        print(f"      {doc.filename}: {count} occurrences")

    # Demonstration 4: Element-level filtering
    print("\n🧩 Element-Level Filtering")
    print("-" * 50)

    for doc in sample_docs:
        if doc.elements:  # Only if we have parsed elements
            print(f"\n📋 Elements in {doc.filename}:")

            # Get elements by type
            element_types = set(elem.element_type for elem in doc.elements)
            for elem_type in element_types:
                type_elements = doc.get_elements_by_type(elem_type)
                print(f"   {elem_type}: {len(type_elements)} elements")

    # Demonstration 5: Advanced filtering patterns for vector DB prep
    print("\n🎯 Vector Database Preparation Patterns")
    print("-" * 50)

    print("🔍 Content filtering for optimal vector storage:")

    # Pattern 1: Filter chunks by content quality
    for doc in sample_docs[:1]:  # Demo with first document
        chunks = doc.get_text_chunks(target_size=300, tolerance=0.15)

        # Filter out very short chunks (might not be useful for vectors)
        quality_chunks = [chunk for chunk in chunks if len(chunk.split()) >= 10]

        # Filter out chunks with too many special characters (might be formatting)
        clean_chunks = []
        for chunk in quality_chunks:
            special_char_ratio = sum(
                1 for c in chunk if not c.isalnum() and not c.isspace()
            ) / len(chunk)
            if special_char_ratio < 0.3:  # Less than 30% special characters
                clean_chunks.append(chunk)

        print(f"   {doc.filename}:")
        print(f"      Original chunks: {len(chunks)}")
        print(f"      After length filter: {len(quality_chunks)}")
        print(f"      After quality filter: {len(clean_chunks)}")

    # Pattern 2: Deduplication for vector storage
    print("\n🔄 Deduplication patterns:")

    all_chunks = []
    for doc in sample_docs:
        chunks = doc.get_text_chunks(target_size=400, tolerance=0.1)
        all_chunks.extend([(chunk, doc.filename) for chunk in chunks])

    # Simple deduplication by exact match
    seen_chunks = set()
    unique_chunks = []

    for chunk, filename in all_chunks:
        chunk_hash = hash(chunk.lower().strip())
        if chunk_hash not in seen_chunks:
            seen_chunks.add(chunk_hash)
            unique_chunks.append((chunk, filename))

    print(f"   Total chunks across all documents: {len(all_chunks)}")
    print(f"   Unique chunks after deduplication: {len(unique_chunks)}")
    print(f"   Deduplication ratio: {len(unique_chunks)/len(all_chunks)*100:.1f}%")

    print(f"\n✨ Search and Filtering Benefits:")
    print("🎯 Precise content discovery before vectorization")
    print("🗂️  Intelligent document filtering by multiple criteria")
    print("🧩 Element-level granular control")
    print("📊 Batch-wide search for comprehensive analysis")
    print("🔄 Deduplication patterns for efficient vector storage")
    print("⚡ Quality filtering for better vector database performance")

    return batch


def demonstrate_content_analysis():
    """
    Demonstrate content analysis and statistics for vector database optimization.
    """

    print("\n📊 Content Analysis and Statistics")
    print("=" * 60)
    print("💡 Use these methods to analyze content before vectorization")
    print("📌 Perfect for understanding document characteristics and optimization")

    # Create a sample document with rich content
    sample_content = textwrap.dedent(
        """
        # AI Development Best Practices Guide
        
        ## Introduction
        
        Artificial intelligence development requires careful planning, robust testing, and continuous monitoring. 
        This comprehensive guide covers essential practices for building reliable AI systems that serve real-world applications.
        
        ## Data Preparation
        
        Quality data is the foundation of successful AI projects. Consider these key factors:
        
        - **Data Quality**: Ensure accuracy, completeness, and consistency
        - **Data Volume**: Collect sufficient samples for training and validation
        - **Data Diversity**: Include representative samples from target populations
        - **Data Privacy**: Implement proper anonymization and security measures
        
        ## Model Development
        
        ### Algorithm Selection
        
        Choose algorithms based on your specific use case:
        
        1. **Classification**: Random Forest, SVM, Neural Networks
        2. **Regression**: Linear Regression, Gradient Boosting, Deep Learning
        3. **Clustering**: K-Means, DBSCAN, Hierarchical Clustering
        4. **Natural Language Processing**: Transformers, BERT, GPT models
        
        ### Training Process
        
        ```python
        # Example training pipeline
        def train_model(data, labels, validation_split=0.2):
            # Split data
            train_data, val_data = split_data(data, validation_split)
            
            # Initialize model
            model = create_model(input_shape=data.shape[1:])
            
            # Configure training
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Train with callbacks
            history = model.fit(
                train_data, 
                validation_data=val_data,
                epochs=100,
                callbacks=[early_stopping, model_checkpoint]
            )
            
            return model, history
        ```
        
        ## Evaluation and Testing
        
        Thorough evaluation ensures model reliability and performance. Use multiple metrics to assess different aspects of model behavior.
        
        ### Performance Metrics
        
        | Metric | Use Case | Formula |
        |--------|----------|---------|
        | Accuracy | General classification | (TP + TN) / (TP + TN + FP + FN) |
        | Precision | When false positives are costly | TP / (TP + FP) |
        | Recall | When false negatives are costly | TP / (TP + FN) |
        | F1-Score | Balanced precision and recall | 2 * (Precision * Recall) / (Precision + Recall) |
        
        ## Deployment Considerations
        
        Production deployment requires additional considerations beyond model performance:
        
        - **Scalability**: Design for expected load and growth
        - **Monitoring**: Track performance, drift, and errors
        - **Rollback**: Maintain ability to revert problematic deployments
        - **Security**: Implement proper authentication and authorization
        
        ## Conclusion
        
        Successful AI development requires a systematic approach combining technical expertise with practical considerations. 
        By following these best practices, teams can build robust, reliable AI systems that deliver value in production environments.
    """
    ).strip()

    # Create document with rich metadata
    doc = Document(
        content=sample_content,
        metadata=DocumentMetadata(
            filename="ai_best_practices.md",
            file_type="markdown",
            total_pages=5,
            total_elements=25,
        ),
    )

    print(f"\n📋 Sample Document: {doc.filename}")
    print(f"📄 Content length: {len(doc.content):,} characters")

    # Demonstration 1: Basic document statistics
    print("\n📈 Document Statistics")
    print("-" * 50)

    stats = doc.get_statistics()

    print(f"📊 Basic metrics:")
    print(f"   Word count: {stats['word_count']:,}")
    print(f"   Content length: {stats['content_length']:,} characters")
    print(f"   Total elements: {stats['total_elements']}")
    print(f"   Total pages: {stats['total_pages']}")

    if stats.get("element_types"):
        print(f"\n🧩 Element type distribution:")
        for elem_type, count in stats["element_types"].items():
            print(f"   {elem_type}: {count}")

    # Demonstration 2: Reading time estimation
    print("\n⏱️ Reading Time Analysis")
    print("-" * 50)

    reading_times = [
        (200, "Average adult reading"),
        (150, "Careful technical reading"),
        (300, "Speed reading"),
        (100, "Complex technical content"),
    ]

    for wpm, description in reading_times:
        time_info = doc.get_reading_time(words_per_minute=wpm)
        print(f"📖 {description} ({wpm} WPM):")
        print(f"   Estimated time: {time_info['minutes']}m {time_info['seconds']}s")

    # Demonstration 3: Key phrase extraction
    print("\n🔑 Key Phrase Extraction")
    print("-" * 50)

    key_phrases = doc.extract_key_phrases(min_length=5, max_phrases=15)

    print("📝 Top key phrases for enhanced vector search:")
    for i, (phrase, frequency) in enumerate(key_phrases[:10], 1):
        print(f"   {i:2d}. '{phrase}' (appears {frequency} times)")

    # Demonstration 4: Language analysis
    print("\n🌐 Language Analysis")
    print("-" * 50)

    lang_info = doc.get_language_info()

    print(f"🔤 Language detection:")
    print(f"   Detected language: {lang_info['language']}")
    print(f"   Confidence: {lang_info['confidence']:.2f}")
    print(f"   Total characters analyzed: {lang_info['total_characters']:,}")

    print(f"\n📊 Character distribution (top 5):")
    for char, freq in list(lang_info["character_distribution"].items())[:5]:
        print(f"   '{char}': {freq:.3f} ({freq*100:.1f}%)")

    # Demonstration 5: Chunking analysis for vector databases
    print("\n🔍 Chunking Analysis for Vector Databases")
    print("-" * 50)

    chunk_configs = [
        (300, 0.1, "Embedding models (300 chars)"),
        (500, 0.15, "Standard retrieval (500 chars)"),
        (800, 0.2, "Context-rich chunks (800 chars)"),
    ]

    print("📏 Chunk size analysis:")

    for target_size, tolerance, purpose in chunk_configs:
        chunks = doc.get_text_chunks(target_size=target_size, tolerance=tolerance)

        if chunks:
            chunk_lengths = [len(chunk) for chunk in chunks]
            avg_length = sum(chunk_lengths) / len(chunk_lengths)
            min_length = min(chunk_lengths)
            max_length = max(chunk_lengths)

            print(f"\n   🎯 {purpose}:")
            print(f"      Chunks generated: {len(chunks)}")
            print(f"      Size range: {min_length}-{max_length} chars")
            print(f"      Average size: {avg_length:.0f} chars")
            print(f"      Size variance: {max_length - min_length} chars")

            # Analyze chunk quality
            word_counts = [len(chunk.split()) for chunk in chunks]
            avg_words = sum(word_counts) / len(word_counts)
            print(f"      Average words per chunk: {avg_words:.1f}")

    # Demonstration 6: Batch content analysis
    print("\n📦 Batch Content Analysis")
    print("-" * 50)

    # Create a small batch for analysis
    sample_docs = [doc]  # In real use, you'd have multiple documents
    batch = DocumentBatch(sample_docs)

    batch_stats = batch.get_statistics()

    print("📊 Batch statistics:")
    print(f"   Total documents: {batch_stats['document_count']}")
    print(f"   Total content length: {batch_stats['total_content_length']:,} chars")
    print(f"   File type distribution: {batch_stats['file_types']}")

    if batch_stats.get("average_metrics"):
        avg_metrics = batch_stats["average_metrics"]
        print(f"\n📈 Average metrics per document:")
        print(f"   Words per document: {avg_metrics['words_per_document']:.0f}")
        print(f"   Pages per document: {avg_metrics['pages_per_document']:.1f}")
        print(f"   Elements per document: {avg_metrics['elements_per_document']:.1f}")

    # Demonstration 7: Content optimization recommendations
    print("\n🎯 Vector Database Optimization Recommendations")
    print("-" * 50)

    # Analyze content for vector database optimization
    word_count = len(doc.content.split())
    char_count = len(doc.content)

    print("💡 Optimization insights:")

    # Recommend optimal chunk size based on content
    if word_count < 200:
        print("   📏 Document is short - consider using smaller chunks (200-300 chars)")
    elif word_count > 2000:
        print(
            "   📏 Document is long - consider larger chunks (800-1000 chars) for context"
        )
    else:
        print("   📏 Document size is optimal - use standard chunks (400-600 chars)")

    # Analyze content complexity
    sentences = doc.content.count(".") + doc.content.count("!") + doc.content.count("?")
    avg_sentence_length = word_count / sentences if sentences > 0 else 0

    if avg_sentence_length > 25:
        print("   🧠 Complex sentences detected - consider overlapping chunks")
    elif avg_sentence_length < 10:
        print("   🧠 Simple sentences - standard chunking should work well")

    # Check for structured content
    if "##" in doc.content and "```" in doc.content:
        print("   📋 Rich markdown structure - use markdown-aware chunking")
    elif "|" in doc.content and "---" in doc.content:
        print("   📊 Tables detected - extract tables separately for structured data")

    print(f"\n✨ Content Analysis Benefits:")
    print("📊 Deep insights into document characteristics")
    print("⏱️ Reading time estimation for user experience")
    print("🔑 Key phrase extraction for enhanced search")
    print("🌐 Language detection for multilingual support")
    print("📏 Optimal chunking recommendations")
    print("🎯 Vector database optimization guidance")

    return doc


def demonstrate_export_formats():
    """
    Demonstrate various export formats for preprocessing and analysis.
    """

    print("\n📋 Export Formats for Preprocessing")
    print("=" * 60)
    print("💡 Use these export formats for custom preprocessing pipelines")
    print("📌 Perfect for integrating with external tools and workflows")

    # Create sample documents with tables and rich content
    doc_with_table = Document(
        content=textwrap.dedent(
            """
        # Product Analysis Report
        
        ## Market Overview
        Our product performance analysis for Q3 2024 shows strong growth across all segments.
        
        ## Sales Performance
        
        | Product | Q3 Sales | Growth | Market Share |
        |---------|----------|--------|--------------|
        | Product A | $2.5M | +23% | 35% |
        | Product B | $1.8M | +15% | 28% |
        | Product C | $1.2M | +31% | 18% |
        | Product D | $0.9M | +8% | 12% |
        
        ## Key Insights
        
        - Product C shows highest growth rate at 31%
        - Market share consolidation continuing
        - Customer acquisition costs decreasing
        
        ## Recommendations
        
        1. Increase investment in Product C marketing
        2. Optimize Product D pricing strategy
        3. Expand Product A distribution channels
        """
        ).strip(),
        metadata=DocumentMetadata(filename="product_analysis.md", file_type="markdown"),
    )

    # Create a batch with multiple documents
    sample_batch = DocumentBatch([doc_with_table])

    print(f"\n📊 Sample Document: {doc_with_table.filename}")
    print(f"📄 Content: {len(doc_with_table.content)} characters")

    # Demonstration 1: Dictionary export for custom processing
    print("\n📋 Dictionary Export")
    print("-" * 50)

    doc_dict = doc_with_table.to_dict()

    print("🗂️ Document as structured dictionary:")
    print(f"   Filename: {doc_dict['metadata']['filename']}")
    print(f"   File type: {doc_dict['metadata']['file_type']}")
    print(f"   Content length: {len(doc_dict['content'])}")
    print(f"   Metadata fields: {list(doc_dict['metadata'].keys())}")
    print(f"   Tables: {len(doc_dict['tables'])}")
    print(f"   Images: {len(doc_dict['images'])}")
    print(f"   Elements: {len(doc_dict['elements'])}")

    # Show how to use dictionary export for custom processing
    print("\n💻 Custom processing example:")
    print(
        textwrap.dedent(
            """
        # Example: Custom preprocessing pipeline
        doc_data = document.to_dict()
        
        # Extract specific metadata for indexing
        metadata = {
            'filename': doc_data['metadata']['filename'],
            'file_type': doc_data['metadata']['file_type'],
            'total_words': len(doc_data['content'].split()),
            'has_tables': len(doc_data['tables']) > 0
        }
        
        # Process content with custom rules
        content = doc_data['content']
        processed_content = apply_custom_preprocessing(content)
        
        # Extract structured data
        tables = doc_data['tables']
        for table in tables:
            structured_data = process_table(table)
    """
        ).strip()
    )

    # Demonstration 2: Markdown export with enhanced formatting
    print("\n📝 Enhanced Markdown Export")
    print("-" * 50)

    markdown_output = doc_with_table.to_markdown()

    print("📄 Enhanced markdown with metadata:")
    print(f"   Output length: {len(markdown_output)} characters")
    print("   Features included:")
    print("   • Document title and metadata section")
    print("   • Table of contents (when applicable)")
    print("   • Preserved formatting and structure")
    print("   • Element-level markdown preservation")

    # Show preview
    lines = markdown_output.split("\n")[:10]
    print(f"\n📖 Preview (first 10 lines):")
    for i, line in enumerate(lines, 1):
        print(f"   {i:2d}: {line}")

    # Demonstration 3: HTML export with styling
    print("\n🌐 HTML Export with Styling")
    print("-" * 50)

    html_output = doc_with_table.to_html()

    print("🎨 HTML export features:")
    print("   • Complete HTML document structure")
    print("   • CSS styling for better presentation")
    print("   • Element-level class annotations")
    print("   • Table formatting preservation")
    print("   • Mobile-responsive design")

    print(f"\n📊 HTML output:")
    print(f"   Length: {len(html_output)} characters")
    print(f"   Contains CSS: {'<style>' in html_output}")
    print(f"   Contains tables: {'<table>' in html_output}")

    # Demonstration 4: Table extraction and export
    print("\n📊 Table Extraction and Export")
    print("-" * 50)

    # Extract table data
    table_data = doc_with_table.extract_table_data()

    print("📋 Table extraction summary:")
    print(f"   Total tables found: {table_data['total_tables']}")
    print(f"   Total rows across all tables: {table_data['total_rows']}")
    print(f"   Tables by page: {table_data['tables_by_page']}")

    if table_data["table_summaries"]:
        print(f"\n📊 Table details:")
        for i, summary in enumerate(table_data["table_summaries"]):
            print(f"   Table {i+1}:")
            print(f"      Rows: {summary['rows']}, Columns: {summary['columns']}")
            print(f"      Has headers: {summary['has_headers']}")
            if summary["caption"]:
                print(f"      Caption: {summary['caption']}")

    # Demonstration 5: Batch export capabilities
    print("\n📦 Batch Export Operations")
    print("-" * 50)

    # Combined text export
    combined_text = sample_batch.to_combined_text()
    print(f"📄 Combined text export:")
    print(f"   Length: {len(combined_text)} characters")
    print(f"   Includes document separators: {'---' in combined_text}")

    # Combined markdown with TOC
    combined_markdown = sample_batch.to_combined_markdown(include_toc=True)
    print(f"\n📝 Combined markdown export:")
    print(f"   Length: {len(combined_markdown)} characters")
    print(f"   Includes table of contents: {include_toc}")
    print(f"   Document navigation: {'Table of Contents' in combined_markdown}")

    # Combined HTML
    combined_html = sample_batch.to_combined_html(include_css=True)
    print(f"\n🌐 Combined HTML export:")
    print(f"   Length: {len(combined_html)} characters")
    print(f"   Includes CSS styling: {'<style>' in combined_html}")
    print(f"   Document structure: {'document-batch' in combined_html}")

    # Batch dictionary export
    batch_dict = sample_batch.to_dict()
    print(f"\n📋 Batch dictionary export:")
    print(f"   Documents: {batch_dict['metadata']['total_documents']}")
    print(f"   Total pages: {batch_dict['metadata']['total_pages']}")
    print(f"   File types: {batch_dict['metadata']['file_types']}")
    print(f"   Metadata fields: {list(batch_dict['metadata'].keys())}")

    # Demonstration 6: Specialized exports for vector databases
    print("\n🗄️ Vector Database Optimized Exports")
    print("-" * 50)

    # Chunked content with metadata for vector storage
    chunked_content = []
    chunks = doc_with_table.get_text_chunks(target_size=400, tolerance=0.15)

    for i, chunk in enumerate(chunks):
        chunk_metadata = {
            "chunk_id": f"{doc_with_table.filename}_{i}",
            "source_document": doc_with_table.filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "content_type": "text",
            "char_count": len(chunk),
            "word_count": len(chunk.split()),
        }

        chunked_content.append({"content": chunk, "metadata": chunk_metadata})

    print(f"🔤 Text chunks for vector storage:")
    print(f"   Total chunks: {len(chunked_content)}")
    print(
        f"   Average size: {sum(len(c['content']) for c in chunked_content) / len(chunked_content):.0f} chars"
    )
    print(
        f"   Metadata fields per chunk: {len(chunked_content[0]['metadata']) if chunked_content else 0}"
    )

    # Markdown chunks with preserved formatting
    md_chunks = doc_with_table.get_markdown_chunks(target_size=500, tolerance=0.2)
    print(f"\n📝 Markdown chunks for vector storage:")
    print(f"   Total chunks: {len(md_chunks)}")
    print(
        f"   Preserves formatting: {any('**' in chunk or '#' in chunk for chunk in md_chunks)}"
    )
    print(f"   Preserves tables: {any('|' in chunk for chunk in md_chunks)}")

    # Demonstration 7: Integration examples
    print("\n🔗 Integration Patterns")
    print("-" * 50)

    print("💡 Export format recommendations by use case:")
    print()
    print("🎯 **Vector Database Storage:**")
    print("   • Use get_text_chunks() or get_markdown_chunks()")
    print("   • Include metadata for enhanced retrieval")
    print("   • Consider chunk size for your embedding model")
    print()
    print("📊 **Data Analysis Pipelines:**")
    print("   • Use to_dict() for structured processing")
    print("   • Extract tables with extract_table_data()")
    print("   • Use batch operations for scale")
    print()
    print("📋 **Documentation Generation:**")
    print("   • Use to_markdown() for technical docs")
    print("   • Use to_html() for web presentation")
    print("   • Use combined exports for multi-document reports")
    print()
    print("🔍 **Search Index Preparation:**")
    print("   • Combine chunked content with search metadata")
    print("   • Use key phrase extraction for enhanced indexing")
    print("   • Consider language detection for multilingual content")

    print(f"\n✨ Export Format Benefits:")
    print("📋 Multiple formats for different use cases")
    print("🎨 Rich formatting preservation where needed")
    print("📊 Structured data extraction (tables, metadata)")
    print("🔄 Batch operations for efficient processing")
    print("🗄️ Vector database optimized outputs")
    print("🔗 Easy integration with external tools")

    return sample_batch


def demonstrate_vector_db_integration():
    """
    Demonstrate vector database integration patterns for major platforms.
    """

    print("\n🗄️ Vector Database Integration Patterns")
    print("=" * 60)
    print("💡 Use these patterns to integrate with popular vector databases")
    print("📌 Production-ready examples for optimal performance")

    # Create sample processed documents
    sample_doc = Document(
        content=SAMPLE_DOCUMENT_DATA["content"],
        metadata=DocumentMetadata(
            filename="annual_report.pdf",
            file_type="pdf",
            total_pages=15,
            total_elements=42,
        ),
    )

    # Example 1: Pinecone Integration Pattern
    print("\n📌 Pinecone Integration Pattern")
    print("-" * 50)
    print(
        textwrap.dedent(
            """
        # Optimal chunk preparation for Pinecone
        from cerevox.document_loader import chunk_text
        import uuid

        def prepare_for_pinecone(document, embedding_model):
            # Get chunks optimized for embedding models (typically 512-1024 tokens)
            chunks = document.get_text_chunks(target_size=512, tolerance=0.15)
            
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = embedding_model.encode(chunk)
                
                # Create Pinecone vector with rich metadata
                vector = {
                    'id': f"{document.filename}_{i}",
                    'values': embedding.tolist(),
                    'metadata': {
                        'content': chunk,
                        'filename': document.filename,
                        'file_type': document.file_type,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'page_count': document.page_count,
                        'char_count': len(chunk),
                        'doc_id': str(uuid.uuid4())
                    }
                }
                vectors_to_upsert.append(vector)
            
            return vectors_to_upsert

        # Usage
        # vectors = prepare_for_pinecone(document, your_embedding_model)
        # pinecone_index.upsert(vectors)
        """
        ).strip()
    )

    # Show actual chunk preparation
    pinecone_chunks = sample_doc.get_text_chunks(target_size=512, tolerance=0.15)
    print(f"✅ Generated {len(pinecone_chunks)} chunks for Pinecone")
    print(
        f"📊 Average chunk size: {sum(len(c) for c in pinecone_chunks)/len(pinecone_chunks):.0f} chars"
    )

    # Example 2: Weaviate Integration Pattern
    print("\n🕸️  Weaviate Integration Pattern")
    print("-" * 50)
    print(
        textwrap.dedent(
            """
        # Weaviate integration with rich document structure
        def prepare_for_weaviate(document):
            # Use markdown chunks to preserve document structure
            chunks = document.get_markdown_chunks(target_size=800, tolerance=0.2)
            
            weaviate_objects = []
            for i, chunk in enumerate(chunks):
                # Weaviate object with comprehensive metadata
                obj = {
                    "content": chunk,
                    "filename": document.filename,
                    "fileType": document.file_type,
                    "chunkIndex": i,
                    "totalChunks": len(chunks),
                    "pageCount": document.page_count,
                    "characterCount": len(chunk),
                    "wordCount": len(chunk.split()),
                    "isMarkdown": True,
                    "hasCodeBlocks": "```" in chunk,
                    "hasHeaders": chunk.strip().startswith('#'),
                    "hasTables": '|' in chunk and '---' in chunk
                }
                weaviate_objects.append(obj)
            
            return weaviate_objects

        # Usage
        # objects = prepare_for_weaviate(document)
        # client.batch.create_objects(objects, class_name="Document")
        """
        ).strip()
    )

    # Show actual chunk preparation for Weaviate
    weaviate_chunks = sample_doc.get_markdown_chunks(target_size=800, tolerance=0.2)
    print(f"✅ Generated {len(weaviate_chunks)} markdown chunks for Weaviate")

    # Analyze chunk characteristics
    has_headers = sum(1 for c in weaviate_chunks if c.strip().startswith("#"))
    has_code = sum(1 for c in weaviate_chunks if "```" in c)
    has_lists = sum(1 for c in weaviate_chunks if "\n-" in c or "\n1." in c)

    print(f"📋 Chunk analysis:")
    print(f"   Chunks with headers: {has_headers}")
    print(f"   Chunks with code blocks: {has_code}")
    print(f"   Chunks with lists: {has_lists}")

    # Example 3: ChromaDB Integration Pattern
    print("\n🎨 ChromaDB Integration Pattern")
    print("-" * 50)
    print(
        textwrap.dedent(
            """
        # ChromaDB batch processing with metadata filtering
        def prepare_for_chromadb(document_batch):
            # Get all chunks with metadata for batch processing
            chunks_with_metadata = document_batch.get_all_text_chunks(
                target_size=600, 
                tolerance=0.15, 
                include_metadata=True
            )
            
            # Prepare ChromaDB batch data
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk_data in enumerate(chunks_with_metadata):
                documents.append(chunk_data['content'])
                
                # Rich metadata for filtering and search
                metadata = {
                    'filename': chunk_data['metadata']['filename'],
                    'chunk_index': chunk_data['metadata']['chunk_index'],
                    'total_chunks': chunk_data['metadata']['total_chunks'],
                    'document_index': chunk_data['metadata']['document_index'],
                    'char_count': len(chunk_data['content']),
                    'word_count': len(chunk_data['content'].split()),
                    'doc_type': 'processed'
                }
                metadatas.append(metadata)
                ids.append(f"chunk_{i}")
            
            return documents, metadatas, ids

        # Usage  
        # docs, metas, ids = prepare_for_chromadb(document_batch)
        # collection.add(documents=docs, metadatas=metas, ids=ids)
        """
        ).strip()
    )

    # Example 4: Qdrant Integration Pattern
    print("\n⚡ Qdrant Integration Pattern")
    print("-" * 50)
    print(
        textwrap.dedent(
            """
        # Qdrant with advanced payload structure
        def prepare_for_qdrant(document):
            # Get element-level chunks with rich metadata (when available)
            chunks = document.get_text_chunks(target_size=500, tolerance=0.1)
            
            points = []
            for i, chunk in enumerate(chunks):
                # Qdrant point with structured payload
                point = {
                    "id": i,
                    "vector": None,  # Will be filled with actual embedding
                    "payload": {
                        "content": chunk,
                        "document": {
                            "filename": document.filename,
                            "file_type": document.file_type,
                            "page_count": document.page_count
                        },
                        "chunk": {
                            "index": i,
                            "total": len(chunks),
                            "size": len(chunk),
                            "words": len(chunk.split())
                        },
                        "features": {
                            "has_numbers": any(c.isdigit() for c in chunk),
                            "has_uppercase": any(c.isupper() for c in chunk),
                            "has_punctuation": any(c in '.,!?;:' for c in chunk),
                            "avg_word_length": sum(len(w) for w in chunk.split()) / len(chunk.split()) if chunk.split() else 0
                        }
                    }
                }
                points.append(point)
            
            return points

        # Usage
        # points = prepare_for_qdrant(document)
        # client.upsert(collection_name="documents", points=points)
        """
        ).strip()
    )

    # Show batch processing example
    print("\n📦 Batch Processing Example")
    print("-" * 50)

    # Create a small batch for demonstration
    docs = [sample_doc]  # In practice, you'd have multiple documents
    batch = DocumentBatch(docs)

    # Get chunks with metadata for vector storage
    batch_chunks = batch.get_all_text_chunks(
        target_size=400, tolerance=0.15, include_metadata=True
    )

    print(f"✅ Batch processing results:")
    print(f"   Total documents: {len(batch)}")
    print(f"   Total chunks generated: {len(batch_chunks)}")
    print(f"   Ready for vector database ingestion")

    # Show metadata structure
    if batch_chunks:
        sample_metadata = batch_chunks[0]["metadata"]
        print(f"\n📋 Sample metadata structure:")
        for key, value in sample_metadata.items():
            print(f"   {key}: {value}")

    print(f"\n🚀 Integration Benefits:")
    print("• 📏 Optimal chunk sizing for embedding models")
    print("• 🏷️  Rich metadata for advanced filtering")
    print("• 🔍 Enhanced search capabilities")
    print("• ⚡ Batch processing efficiency")
    print("• 🧠 Document structure preservation")
    print("• 📊 Analytics-ready metadata")

    return batch_chunks


def demonstrate_validation_and_error_handling():
    """
    Demonstrate validation and error handling for robust vector database preparation.
    """

    print("\n🛡️ Validation and Error Handling")
    print("=" * 60)
    print("💡 Use these patterns to ensure robust vector database preparation")
    print("📌 Perfect for production systems and reliable data processing")

    # Demonstration 1: Document validation
    print("\n🔍 Document Validation")
    print("-" * 50)

    # Create valid document
    valid_doc = Document(
        content="This is a valid document with proper content.",
        metadata=DocumentMetadata(filename="valid_document.txt", file_type="text"),
    )

    # Validate valid document
    validation_errors = valid_doc.validate()
    print(f"✅ Valid document validation:")
    print(f"   Filename: {valid_doc.filename}")
    print(f"   Validation errors: {len(validation_errors)}")
    if validation_errors:
        for error in validation_errors:
            print(f"      ❌ {error}")
    else:
        print("   ✅ All validation checks passed")

    # Demonstration 2: Handling malformed data
    print("\n⚠️ Handling Malformed Data")
    print("-" * 50)

    print("🧪 Testing various error conditions:")

    # Test 1: Missing metadata
    try:
        invalid_doc = Document(
            content="Content without proper metadata",
            metadata=None,  # This will cause issues
        )
    except Exception as e:
        print(f"   ❌ Missing metadata: Handled gracefully - {type(e).__name__}")

    # Test 2: Empty content handling
    try:
        empty_doc = Document(
            content="",
            metadata=DocumentMetadata(filename="empty.txt", file_type="text"),
        )
        chunks = empty_doc.get_text_chunks()
        print(f"   ✅ Empty content: {len(chunks)} chunks (graceful handling)")
    except Exception as e:
        print(f"   ❌ Empty content error: {e}")

    # Test 3: Invalid chunk parameters
    try:
        chunks = valid_doc.get_text_chunks(target_size=-100)  # Invalid size
        print(
            f"   ⚠️ Invalid chunk size: Generated {len(chunks)} chunks (fallback used)"
        )
    except Exception as e:
        print(f"   ❌ Invalid chunk size error: {e}")

    # Demonstration 3: Batch validation
    print("\n📦 Batch Validation")
    print("-" * 50)

    # Create valid and invalid documents for batch
    valid_docs = [
        Document(
            content="First valid document",
            metadata=DocumentMetadata(filename="doc1.txt", file_type="text"),
        ),
        Document(
            content="Second valid document",
            metadata=DocumentMetadata(filename="doc2.txt", file_type="text"),
        ),
    ]

    # Create batch and validate
    batch = DocumentBatch(valid_docs)
    batch_errors = batch.validate()

    print(f"📊 Batch validation results:")
    print(f"   Documents in batch: {len(batch)}")
    print(f"   Validation errors: {len(batch_errors)}")

    if batch_errors:
        print("   ❌ Validation issues found:")
        for error in batch_errors:
            print(f"      • {error}")
    else:
        print("   ✅ All batch validation checks passed")

    # Demonstration 4: Chunking error handling
    print("\n🔧 Chunking Error Handling")
    print("-" * 50)

    # Test various problematic content
    test_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("A" * 10000, "Very long content"),
        ("Short", "Very short content"),
        ("Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?", "Special characters"),
        ("Unicode: 你好世界 🌍 🚀", "Unicode content"),
    ]

    print("🧪 Testing chunking with various content types:")

    for content, description in test_cases:
        try:
            doc = Document(
                content=content,
                metadata=DocumentMetadata(
                    filename=f"test_{description.lower().replace(' ', '_')}.txt",
                    file_type="text",
                ),
            )

            # Test both text and markdown chunking
            text_chunks = doc.get_text_chunks(target_size=50, tolerance=0.2)
            md_chunks = doc.get_markdown_chunks(target_size=50, tolerance=0.2)

            print(f"   ✅ {description}:")
            print(f"      Text chunks: {len(text_chunks)}")
            print(f"      Markdown chunks: {len(md_chunks)}")

        except Exception as e:
            print(f"   ❌ {description}: {type(e).__name__} - {e}")

    # Demonstration 5: API response error handling
    print("\n📡 API Response Error Handling")
    print("-" * 50)

    # Simulate various API response scenarios
    test_responses = [
        ({}, "Empty response"),
        ({"data": []}, "Empty data array"),
        ({"documents": []}, "Empty documents array"),
        ({"error": "API Error"}, "Error response"),
        (None, "None response"),
    ]

    print("🌐 Testing API response handling:")

    for response_data, description in test_responses:
        try:
            if response_data is None:
                print(f"   ⚠️ {description}: Skipped (None response)")
                continue

            # Try to create document from API response
            doc = Document.from_api_response(
                response_data,
                filename=f"test_{description.lower().replace(' ', '_')}.txt",
            )

            print(f"   ✅ {description}:")
            print(f"      Document created: {doc.filename}")
            print(f"      Content length: {len(doc.content)}")

        except Exception as e:
            print(f"   ❌ {description}: {type(e).__name__} - {e}")

    # Demonstration 6: Production-ready error patterns
    print("\n🏭 Production-Ready Error Patterns")
    print("-" * 50)

    print("💡 Recommended error handling patterns:")

    # Pattern 1: Safe chunking with fallbacks
    print("\n🔧 Safe chunking pattern:")
    print(
        textwrap.dedent(
            """
        def safe_chunk_document(document, target_size=500, tolerance=0.1):
            try:
                # Attempt primary chunking method
                chunks = document.get_text_chunks(target_size, tolerance)
                
                # Validate chunks
                if not chunks or len(chunks) == 0:
                    # Fallback: simple split
                    content = document.content or ""
                    chunks = [content[i:i+target_size] 
                             for i in range(0, len(content), target_size)]
                
                # Filter empty chunks
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
                
                return chunks
                
            except Exception as e:
                # Log error and return fallback
                print(f"Chunking error: {e}")
                return [document.content] if document.content else []
    """
        ).strip()
    )

    # Pattern 2: Batch processing with error collection
    print("\n📦 Robust batch processing:")
    print(
        textwrap.dedent(
            """
        def process_batch_safely(documents):
            results = []
            errors = []
            
            for i, doc in enumerate(documents):
                try:
                    # Validate document first
                    validation_errors = doc.validate()
                    if validation_errors:
                        errors.append(f"Doc {i}: {validation_errors}")
                        continue
                    
                    # Process document
                    chunks = doc.get_text_chunks()
                    results.append({
                        'document': doc,
                        'chunks': chunks,
                        'status': 'success'
                    })
                    
                except Exception as e:
                    errors.append(f"Doc {i} ({doc.filename}): {e}")
                    results.append({
                        'document': doc,
                        'chunks': [],
                        'status': 'error',
                        'error': str(e)
                    })
            
            return results, errors
    """
        ).strip()
    )

    # Pattern 3: Graceful degradation
    print("\n🎯 Graceful degradation pattern:")
    print(
        textwrap.dedent(
            """
        def prepare_for_vector_db(document, preferred_format='markdown'):
            # Try preferred format first
            try:
                if preferred_format == 'markdown':
                    return document.get_markdown_chunks()
                else:
                    return document.get_text_chunks()
            except Exception:
                pass
            
            # Fallback to basic text chunking
            try:
                return document.get_text_chunks()
            except Exception:
                pass
            
            # Last resort: return whole content
            return [document.content] if document.content else []
    """
        ).strip()
    )

    # Demonstration 7: Error monitoring and logging
    print("\n📊 Error Monitoring Best Practices")
    print("-" * 50)

    print("📈 Monitoring recommendations:")
    print("   • Track chunking success rates")
    print("   • Monitor chunk size distributions")
    print("   • Log validation failures")
    print("   • Track processing times")
    print("   • Monitor memory usage for large batches")
    print("   • Alert on consecutive failures")

    print("\n🔍 Common error categories to monitor:")
    print("   • Malformed API responses")
    print("   • Content encoding issues")
    print("   • Memory exhaustion with large documents")
    print("   • Invalid chunk size parameters")
    print("   • Missing or corrupted metadata")
    print("   • Network timeouts during processing")

    print(f"\n✨ Validation and Error Handling Benefits:")
    print("🛡️ Robust error handling for production systems")
    print("🔍 Comprehensive validation for data quality")
    print("🎯 Graceful degradation for reliability")
    print("📊 Error monitoring and alerting patterns")
    print("🔧 Safe fallback mechanisms")
    print("💪 Production-ready resilience")


def demonstrate_competitive_advantages():
    """
    Show how Cerevox document_loader compares to competitive solutions.
    """

    print("\n🏆 Competitive Comparison")
    print("=" * 60)

    print("\n🎯 Cerevox Advantages:")
    print("• 🧠 Semantic-aware chunking respects document structure")
    print("• 📏 Precise size control with configurable tolerance (±%)")
    print("• 🎨 Markdown formatting preservation for better context")
    print("• 💻 Code block integrity maintained in chunks")
    print("• 📊 Rich metadata for enhanced retrieval and filtering")
    print("• 🚀 Built-in vector database preparation")
    print("• 🗄️ Direct integration patterns for popular vector DBs")
    print("• 🔍 Advanced element-level chunking with metadata")
    print("• 📦 Efficient batch processing capabilities")
    print("• ⚡ Production-ready performance optimization")


def main():
    """Run all vector database preparation demonstrations"""

    print("🚀 Cerevox Vector Database Preparation Suite")
    print("=" * 80)
    print("The most accurate document chunking for vector databases")
    print("=" * 80)

    # Run demonstrations in logical order
    print("\n🎯 This demo will show you:")
    print("1. 🧩 Element-level chunking with rich metadata")
    print("2. 🚀 Document-level chunking methods")
    print("3. 📦 Batch operations for multiple documents")
    print("4. 🛠️  Standalone chunking functions")
    print("5. 🔍 Search and filtering capabilities")
    print("6. 📊 Content analysis and statistics")
    print("7. 📋 Export formats for preprocessing")
    print("8. 🗄️  Vector database integration patterns")
    print("9. 🛡️  Validation and error handling")
    print("10. 🏆 Competitive advantages")

    try:
        # Core functionality demonstrations
        elements = demonstrate_element_chunking()
        document_chunks = demonstrate_document_chunking()
        batch = demonstrate_batch_operations()
        standalone_chunks = demonstrate_standalone_chunking()
        search_and_filtering = demonstrate_search_and_filtering()
        content_analysis = demonstrate_content_analysis()
        export_formats = demonstrate_export_formats()
        vector_chunks = demonstrate_vector_db_integration()
        demonstrate_validation_and_error_handling()
        demonstrate_competitive_advantages()

        # Summary
        print("\n✨ Demo Complete - Key Takeaways:")
        print("=" * 60)
        print("🧩 Element chunking: Rich metadata with element-level context")
        print("📄 Document chunking: Smart, size-controlled, format-aware")
        print("📦 Batch processing: Efficient multi-document handling")
        print("🛠️  Standalone functions: Flexible text processing")
        print("🔍 Search & filtering: Advanced content discovery")
        print("📊 Content analysis: Deep document insights")
        print("📋 Export formats: Multiple preprocessing options")
        print("🗄️  Vector DB integration: Production-ready patterns")
        print("🛡️  Validation: Robust error handling")
        print("🏆 Competitive edge: Advanced features unmatched by competitors")

        print("\n🚀 Ready to revolutionize your vector database workflow!")
        print("📚 Visit our documentation for more examples and integration guides")
        print("💬 Join our community for support and best practices")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print(
            "💡 This is a demonstration script - some features require actual API integration"
        )


if __name__ == "__main__":
    main()
