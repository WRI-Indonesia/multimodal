import geopandas as gpd
import zipfile
from pathlib import Path
from streamlit.runtime.uploaded_file_manager import UploadedFile


def read_uploaded_file(uploaded_file: UploadedFile) -> gpd.GeoDataFrame:
    try:
        if uploaded_file.name.endswith((".geojson", ".json")):
            # Use BytesIO for in-memory file handling
            gdf: gpd.GeoDataFrame = gpd.read_file(uploaded_file.getvalue())  # type: ignore

        elif uploaded_file.name.endswith(".shp.zip"):
            # Create temp directory if it doesn't exist
            temp_dir = Path("/tmp/shp")
            temp_dir.mkdir(exist_ok=True, parents=True)

            # Write and extract zip
            zip_path = Path(f"/tmp/{uploaded_file.name}")
            with zip_path.open("wb") as f:
                f.write(uploaded_file.getbuffer())

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the first .shp file in the extracted dir
            shp_files = list(temp_dir.glob("*.shp"))
            if not shp_files:
                raise ValueError("No .shp file found in the zip archive")

            gdf = gpd.read_file(shp_files[0])  # type: ignore

        else:
            raise ValueError(
                "Unsupported file format. Expected .geojson, .json, or .shp.zip"
            )

        return gdf

    except Exception as e:
        raise RuntimeError(f"Failed to process uploaded file: {str(e)}") from e
