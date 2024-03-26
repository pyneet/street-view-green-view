"""Assign Green View score to point features"""

import os
import cv2
import geopandas as gpd
import numpy as np
import pandas as pd
from skimage.filters import threshold_otsu
import typer

app = typer.Typer()


def get_gvi_score(image_path):
    """
    Calculate the Green View Index (GVI) for a given image file.

    Args:
        image_path (str): Path to the image file.

    Returns:
        float: The Green View Index (GVI) score for the given image.
    """
    # Load the image
    original_image = cv2.imread(image_path)

    # Convert to RGB color space
    rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

    # Calculate ExG (Excess Green)
    r, g, b = cv2.split(rgb_image.astype(np.float32) / 255)
    exg = 2 * g - r - b

    # Apply Otsu's thresholding on ExG
    threshold = threshold_otsu(exg)
    green_pixels = (exg > threshold).sum()
    total_pixels = original_image.shape[0] * original_image.shape[1]

    # Calculate the Green View Index (GVI)
    gvi_score = (green_pixels / total_pixels) * 100

    return gvi_score


@app.command()
def main(image_directory, interim_data, output_file):
    """

    Args:
            image_directory: directory path for folder holding Mapillary images
            interim_data: file holding interim data (output from create_points.py)
            output_file: file to save GeoPackage output to (provide full path)

    Returns:
            File containing point locations with associated Green View score

    """
    # Check image directory exists
    if os.path.exists(image_directory):
        pass
    else:
        raise ValueError("Image directory could not be found")
    # Check image directory contains image files
    # (This is based on the jpeg export in download_images.py)
    if ".jpeg" in "\t".join(os.listdir(os.path.join(image_directory))):
        pass
    else:
        raise Exception(
            "Image directory doesn't contain expected contents (.jpeg files)"
        )
    # Check interim data is valid
    # Point data
    if "Point" in gpd.read_file(interim_data).geometry.type.unique():
        pass
    else:
        raise Exception("Expected point data in interim data file but none found")

    # Make an empty dataframe to hold the data
    df = pd.DataFrame({"filename": [], "gvi_score": []})

    # Loop through each image in the Mapillary folder and get the GVI score
    for i in os.listdir(image_directory):
        gvi_score = get_gvi_score(os.path.join(image_directory, i))

        temp_df = pd.DataFrame({"filename": [i], "gvi_score": [gvi_score]})

        print(i, "\t", str(gvi_score))

        df = pd.concat([df, temp_df], ignore_index=True)

    # Create an image ID from the file name, to match to the point dataset
    df["image_id"] = df["filename"].str[:-5]

    # Open the interim point data
    gdf = gpd.read_file(interim_data)

    # Join the GVI score to the interim point data using the `image id` attribute
    gdf = gdf.merge(df, how="left", on="image_id")

    # Print how many records were matched on each side

    # Export as GPKG
    gdf.to_file(output_file)


if __name__ == "__main__":
    app()
