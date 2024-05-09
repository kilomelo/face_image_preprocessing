import os
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

def count_extensions(directory):
    """Counts file extensions in the given directory, including subdirectories, and displays a dynamic counter."""
    extension_count = defaultdict(int)
    total_files = 0

    # Create a dynamic counter with tqdm without a set total
    pbar = tqdm(desc="Counting files")

    # Walk through the directory and process files
    for root, _, files in os.walk(directory):
        for file in files:
            ext = Path(file).suffix.lower()  # Get file extension and convert to lowercase
            extension_count[ext] += 1
            total_files += 1
            pbar.update(1)  # Update the counter per file processed

    pbar.close()  # Close the progress bar after all files have been processed
    return extension_count, total_files

def save_results(directory, extension_count, total_files):
    """Saves the extension count results to a text file in the given directory."""
    output_file = Path(directory) / "extension_summary.txt"
    with open(output_file, 'w') as file:
        file.write(f"Total files: {total_files}\n")
        file.write(f"Unique extensions: {len(extension_count)}\n")
        for ext, count in sorted(extension_count.items()):
            file.write(f"{ext}: {count}\n")

def main(directory):
    """Main function to handle the workflow."""
    tqdm.write(f"Starting scan of directory: {directory}")

    # Count extensions and dynamically update the count
    extension_count, total_files = count_extensions(directory)

    # Save results
    save_results(directory, extension_count, total_files)
    tqdm.write(f"Results saved to {directory}/extension_summary.txt")

    # Output final summary
    tqdm.write(f"Total files processed: {total_files}")
    tqdm.write(f"Unique extensions found: {len(extension_count)}")
    for ext, count in sorted(extension_count.items()):
        tqdm.write(f"Extension '{ext}': {count} files")

directory = "/Volumes/192.168.1.173/pic/韩国美女模特写真集_1375[1186_MB]"
main(directory)