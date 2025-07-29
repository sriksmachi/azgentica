#!/usr/bin/env python3
"""
WAF Recommendations Data Pipeline

This script processes Azure Well-Architected Framework documents using Azure Document Intelligence
to extract architecture best practices and recommendations, then structures them into a CSV format.

Requirements:
- Azure Document Intelligence service endpoint and key
- Environment variables: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY
- Input PDF: data/azure-well-architected.pdf
"""

import os
import pandas as pd
import uuid
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv


def setup_document_intelligence_client():
    """Initialize Azure Document Intelligence client with credentials from environment variables."""
    load_dotenv()

    di_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    di_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not di_endpoint or not di_key:
        raise ValueError(
            "Missing required environment variables: "
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY"
        )

    di_credential = AzureKeyCredential(di_key)
    return DocumentIntelligenceClient(di_endpoint, di_credential)


def analyze_document(client, file_path):
    """Analyze PDF document using Azure Document Intelligence prebuilt-layout model."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sample document not found at {file_path}")

    print(f"Analyzing document: {file_path}")

    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", body=f)

    result = poller.result()
    print(
        f"Document analysis completed. Found {len(result.paragraphs)} paragraphs.")

    return result


def extract_architecture_best_practices(result):
    """
    Extract architecture best practices from document analysis results.

    Structures the documents as Pages -> Paragraphs -> Text based on headings
    that contain "Architecture best practices for".
    """
    pages = []
    current_page = None

    for paragraph in result.paragraphs:
        role = paragraph.get("role", "paragraph")
        content = paragraph.get("content", "")

        # If a title with "Architecture best practices for" is found, create a new page
        if "Architecture best practices for" in content and role == "title":
            # Create new page for this architecture best practice section
            current_page = {
                "id": str(uuid.uuid4()),
                "heading": content,
                "content": content
            }
            pages.append(current_page)
            print(f"Found new section: {content}")

        elif current_page is not None:
            # Add content to the current page
            current_page["content"] += f"\n{content}"

    print(f"Extracted {len(pages)} architecture best practices documents.")
    return pages


def save_to_csv(pages, output_path):
    """Save extracted pages to CSV file."""
    if not pages:
        print("No pages to save.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert to DataFrame and save
    df = pd.DataFrame(pages)
    df.to_csv(output_path, index=False)

    print(f"Saved {len(pages)} pages to {output_path}")

    # Display summary statistics
    print("\nSummary:")
    print(f"- Total sections: {len(df)}")
    print(
        f"- Average content length: {df['content'].str.len().mean():.0f} characters")
    print(f"- Longest section: {df['content'].str.len().max()} characters")
    print(f"- Shortest section: {df['content'].str.len().min()} characters")


def main():
    """Main pipeline execution."""
    # Configuration
    input_file = "data/azure-well-architected.pdf"
    output_file = "data/azure-service-recommendations.csv"

    try:
        print("="*60)
        print("WAF Recommendations Data Pipeline")
        print("="*60)

        # Step 1: Setup Azure Document Intelligence client
        print("1. Setting up Azure Document Intelligence client...")
        client = setup_document_intelligence_client()

        # Step 2: Analyze document
        print("2. Analyzing PDF document...")
        result = analyze_document(client, input_file)

        # Step 3: Extract architecture best practices
        print("3. Extracting architecture best practices...")
        pages = extract_architecture_best_practices(result)

        # Step 4: Save to CSV
        print("4. Saving results to CSV...")
        save_to_csv(pages, output_file)

        print("\n" + "="*60)
        print("Pipeline completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"Error in pipeline: {str(e)}")
        raise


if __name__ == "__main__":
    main()
