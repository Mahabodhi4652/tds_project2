import os
import sys
import pandas as pd
import seaborn
import matplotlib.pyplot as matplotlib_pyplot
import httpx
import chardet
import time
from concurrent.futures import ThreadPoolExecutor

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")  # Using environment variable for token
MAX_ROWS = 5000  # Limit the dataset size for faster processing

def load_data(file_path):
    """Load CSV data with encoding detection and limit rows to MAX_ROWS."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    df = pd.read_csv(file_path, encoding=encoding)
    return df.head(MAX_ROWS)  # Limit the dataset to MAX_ROWS

def analyze_data(df):
    """Perform advanced data analysis."""
    numeric_df = df.select_dtypes(include=['number'])
    categorical_df = df.select_dtypes(include=['object', 'category'])

    analysis = {
        'numeric_summary': numeric_df.describe().to_dict(),
        'categorical_summary': categorical_df.describe().to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict(),
        'skewness': numeric_df.skew().to_dict(),
        'kurtosis': numeric_df.kurt().to_dict()
    }
    return analysis

def visualize_advanced(df, output_folder):
    """Generate simplified visualizations to speed up processing."""
    seaborn.set(style="whitegrid")

    # Only create a pairplot if there are fewer than 5 numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) < 5:
        seaborn.pairplot(df[numeric_columns])
        pairplot_path = os.path.join(output_folder, "pairplot.png")
        matplotlib_pyplot.savefig(pairplot_path)
        matplotlib_pyplot.close()

    # Box plot to check for outliers (only top 3 numeric columns)
    for column in numeric_columns[:3]:
        matplotlib_pyplot.figure(figsize=(8, 6))
        seaborn.boxplot(data=df, x=column)
        boxplot_path = os.path.join(output_folder, f"boxplot_{column}.png")
        matplotlib_pyplot.savefig(boxplot_path)
        matplotlib_pyplot.close()

    print(f"Visualizations saved to {output_folder}")

def generate_detailed_narrative(df, analysis):
    """Generate a detailed narrative using LLM with dynamic prompts."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Create a more dynamic prompt based on the data analysis
    prompt = f"""
        Analyze the dataset with the following columns: {', '.join(df.columns)}.
        Please break the analysis into sections:
        1. **Overview**: Provide a brief description of the dataset.
        2. **Numeric Analysis**: Highlight key statistics (mean, variance, skewness, kurtosis) and discuss trends.
        3. **Categorical Analysis**: Mention most frequent values and potential anomalies.
        4. **Correlations**: Discuss relationships between numeric features and potential outliers.
        5. **Advanced Insights**: Offer any deeper insights or hypotheses that can be tested further.

        Include markdown formatting for structure and clarity.
    """

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:  # Set timeout for HTTP request
            response = client.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Narrative generation failed due to an error."

def generate_dynamic_narrative(df, analysis):
    """Generate a dynamic narrative based on real-time data analysis."""
    missing_data = df.isnull().sum().to_dict()
    skewness = df.select_dtypes(include=['number']).skew().to_dict()

    prompt = f"""
        Provide an analysis of the dataset with the following columns: {', '.join(df.columns)}. 
        The dataset has missing values in the following columns: {', '.join([col for col, val in missing_data.items() if val > 0])}. 
        The skewness values for numeric columns are: {', '.join([f"{col}: {val:.2f}" for col, val in skewness.items()])}.
        Discuss the impact of these observations and suggest potential next steps for data preprocessing.
    """

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        with httpx.Client(timeout=30.0) as client:  # Set timeout for HTTP request
            response = client.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Dynamic narrative generation failed due to an error."

def main(file_path):
    start_time = time.time()  # Start timer for performance tracking
    df = load_data(file_path)
    analysis = analyze_data(df)

    # Create output folder
    output_folder = os.path.join(os.getcwd(), os.path.basename(file_path).replace(".csv", ""))
    os.makedirs(output_folder, exist_ok=True)

    # Generate and save advanced visualizations
    visualize_advanced(df, output_folder)

    # Generate dynamic narrative
    findings = generate_dynamic_narrative(df, analysis)

    # Save narrative to README.md
    with open(os.path.join(output_folder, "README.md"), "w") as f:
        f.write("# Dataset Analysis Results\n\n")
        f.write(f"### Insights:\n{findings}")

    print(f"Analysis completed. Check the output folder: {output_folder}")
    
    # Ensure the script completes in less than 120 seconds
    elapsed_time = time.time() - start_time
    if elapsed_time > 120:
        print(f"Warning: The script took {elapsed_time:.2f} seconds to complete, which exceeds the 120-second limit.")
    else:
        print(f"Script completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])
