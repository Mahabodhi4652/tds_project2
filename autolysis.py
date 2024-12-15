import os
import sys
import time
import importlib
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy import stats
from sklearn.ensemble import IsolationForest

# Function to check and import required libraries
def check_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        return importlib.import_module(import_name)
    except ImportError as e:
        print(f"Error: {import_name} is not installed. Please install it manually using:")
        print(f"  pip install {package}")
        sys.exit(1)

# Required packages
required_packages = {
    "pandas": "pandas",
    "numpy": "numpy",
    "seaborn": "seaborn",
    "matplotlib": "matplotlib",
    "httpx": "httpx",
    "chardet": "chardet",
    "scikit-learn": "sklearn",
    "scipy": "scipy",
}

# Import all required packages
for package, import_name in required_packages.items():
    globals()[import_name] = check_and_import(package, import_name)

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')  # Token from environment variable

# Function to load CSV data
def load_data(file_path):
    """Load CSV data with encoding detection."""
    start_time = time.time()
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    df = pd.read_csv(file_path, encoding=encoding)
    print(f"Data loaded in {time.time() - start_time:.2f} seconds.")
    return df

# Function for advanced analysis with sophisticated outlier detection
def advanced_analysis(df):
    """Perform advanced data analysis with outlier detection."""
    start_time = time.time()

    # Handle missing values (improving strategy for different data types)
    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].fillna(df[column].mode()[0])  # Fill categorical missing values with mode
        else:
            df[column] = df[column].fillna(df[column].mean())  # Fill numerical missing values with mean

    # Sophisticated outlier detection using Isolation Forest
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    outliers = iso_forest.fit_predict(df[numeric_columns].dropna())
    outliers = np.where(outliers == -1)[0]  # Outliers are marked as -1 by Isolation Forest

    # Scaling numeric data for PCA and clustering
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df[numeric_columns]), columns=numeric_columns)

    # PCA for dimensionality reduction
    pca = PCA(n_components=2)
    pca_components = pca.fit_transform(df_scaled)
    pca_df = pd.DataFrame(pca_components, columns=["PCA1", "PCA2"])

    # KMeans Clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['Cluster'] = kmeans.fit_predict(df_scaled)

    # Add PCA components to df for visualization
    df['PCA1'] = pca_df['PCA1']
    df['PCA2'] = pca_df['PCA2']

    print(f"Advanced analysis completed in {time.time() - start_time:.2f} seconds.")
    return {
        'outliers': outliers,
        'pca_components': pca_df,
        'clusters': df['Cluster'].value_counts().to_dict()
    }

def create_visualizations(df, output_folder):
    """Generate dynamic visualizations for analysis with labels and titles."""
    start_time = time.time()
    numeric_columns = df.select_dtypes(include=['number']).columns

    if len(numeric_columns) > 0:
        # Histograms for numeric columns with labels
        fig, axes = plt.subplots(1, len(numeric_columns), figsize=(15, 5))
        for i, column in enumerate(numeric_columns):
            axes[i].hist(df[column].dropna(), bins=30, alpha=0.7)
            axes[i].set_title(f'{column} Distribution')
            axes[i].set_xlabel(f'{column}')
            axes[i].set_ylabel('Frequency')

        plt.tight_layout()
        hist_path = os.path.join(output_folder, "numeric_histograms.png")
        plt.savefig(hist_path)
        plt.close()

        # Correlation heatmap with labels and title
        corr_matrix = df[numeric_columns].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
        ax.set_title('Correlation Heatmap')
        heatmap_path = os.path.join(output_folder, "correlation_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()

        # PCA scatter plot with labels and title
        fig, ax = plt.subplots(figsize=(8, 6))
        scatter = ax.scatter(df['PCA1'], df['PCA2'], c=df['Cluster'], cmap='viridis')
        ax.set_title('PCA Components and Clusters')
        ax.set_xlabel('PCA1')
        ax.set_ylabel('PCA2')
        plt.colorbar(scatter)
        pca_path = os.path.join(output_folder, "pca_plot.png")
        plt.savefig(pca_path)
        plt.close()

        print(f"Visualizations saved in {time.time() - start_time:.2f} seconds.")
    else:
        print("No numeric columns found for visualization.")

def generate_dynamic_narrative(df, analysis, output_folder):
    """Generate dynamic narrative with improved structure and integration of visualizations."""
    start_time = time.time()
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }

    numeric_columns = df.select_dtypes(include=['number']).columns
    prompt = f"Analyze the dataset with the following numeric columns: {', '.join(numeric_columns)}. "

    # Add insights from PCA, clustering, and outliers dynamically
    if 'pca_components' in analysis:
        prompt += f"The PCA analysis suggests the following components: {analysis['pca_components'].head(5).to_dict()}. "
    if 'clusters' in analysis:
        prompt += f"The KMeans clustering results indicate {len(analysis['clusters'])} clusters. "
    if 'outliers' in analysis:
        prompt += f"Outliers have been detected in the dataset with the following indices: {', '.join(map(str, analysis['outliers']))}."

    prompt += "Please provide insights into how these results contribute to understanding the dataset and how they could be relevant for decision-making."

    # Integrating visualizations into the narrative
    prompt += f"Refer to the visualizations saved as {output_folder}/numeric_histograms.png, {output_folder}/correlation_heatmap.png, and {output_folder}/pca_plot.png."

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        with httpx.Client() as client:
            response = client.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        narrative = response.json()['choices'][0]['message']['content']
        print(f"Narrative generated in {time.time() - start_time:.2f} seconds.")
        return narrative
    except Exception as e:
        print(f"Error generating narrative: {e}")
        return "Failed to generate narrative."

def main(file_path):
    """Main function to run the analysis."""
    overall_start = time.time()

    # Load and analyze the dataset
    df = load_data(file_path)
    analysis = advanced_analysis(df)

    # Prepare output folder
    base_name = os.path.basename(file_path)
    output_folder = os.path.join(os.getcwd(), base_name[:-4])
    os.makedirs(output_folder, exist_ok=True)

    # Generate visualizations
    create_visualizations(df, output_folder)

    # Generate narrative and save to README
    findings = generate_dynamic_narrative(df, analysis, output_folder)  # Pass output_folder here
    readme_path = os.path.join(output_folder, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Analysis Results\n\n")
        f.write(f"## Key Insights\n\n{findings}\n")

    print(f"Total execution time: {time.time() - overall_start:.2f} seconds.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])
