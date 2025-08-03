#!/usr/bin/env python3
"""
WAF Recommendations Data Pipeline CLI

This script processes Azure Well-Architected Framework documents using Azure Document Intelligence
to extract architecture best practices and recommendations, then structures them into a CSV format.

Requirements:
- Azure Document Intelligence service endpoint and key
- Environment variables: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY
- Input PDF: data/azure-well-architected.pdf
"""

import os
import uuid
import click
import pandas as pd
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
    click.echo(f"Analyzing document: {file_path}")
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()
    click.echo(
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
        if (("Architecture best practices for" in content) or ("Azure Well-Architected Framework perspective" in content)) and role == "title":
            current_page = {
                "id": str(uuid.uuid4()),
                "heading": content,
                "content": content
            }
            pages.append(current_page)
            click.echo(f"Found new section: {content}")
        elif current_page is not None:
            current_page["content"] += f"\n{content}"
    click.echo(
        f"Extracted {len(pages)} architecture best practices documents.")
    return pages


def save_to_csv(pages, output_path):
    """Save extracted pages to CSV file."""
    if not pages:
        click.echo("No pages to save.")
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(pages)
    df.to_csv(output_path, index=False)
    click.echo(f"Saved {len(pages)} pages to {output_path}")
    click.echo("\nSummary:")
    click.echo(f"- Total sections: {len(df)}")
    click.echo(
        f"- Average content length: {df['content'].str.len().mean():.0f} characters")
    click.echo(
        f"- Longest section: {df['content'].str.len().max()} characters")
    click.echo(
        f"- Shortest section: {df['content'].str.len().min()} characters")


@click.command()
@click.option(
    "--input-file", "-i",
    default="data/azure-well-architected.pdf",
    show_default=True,
    help="Path to the input PDF file."
)
@click.option(
    "--output-file", "-o",
    default="data/azure-service-recommendations.csv",
    show_default=True,
    help="Path to the output CSV file."
)
def cli(input_file, output_file):
    """WAF Recommendations Data Pipeline CLI."""
    click.secho("="*60, fg="cyan")
    click.secho("WAF Recommendations Data Pipeline", fg="green", bold=True)
    click.secho("="*60, fg="cyan")
    try:
        click.secho(
            "1. Setting up Azure Document Intelligence client...", fg="yellow")
        client = setup_document_intelligence_client()
        click.secho("2. Analyzing PDF document...", fg="yellow")
        result = analyze_document(client, input_file)
        click.secho("3. Extracting architecture best practices...", fg="yellow")
        pages = extract_architecture_best_practices(result)
        click.secho("4. Saving results to CSV...", fg="yellow")
        save_to_csv(pages, output_file)
        click.secho("\n" + "="*60, fg="cyan")
        click.secho("Pipeline completed successfully!", fg="green", bold=True)
        click.secho("="*60, fg="cyan")
    except Exception as e:
        click.secho(f"Error in pipeline: {str(e)}", fg="red")
        raise


if __name__ == "__main__":
    cli()
