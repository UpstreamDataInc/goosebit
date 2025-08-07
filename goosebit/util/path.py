from anyio import Path


async def validate_filename(filename: str, temp_dir: Path) -> Path:
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")

    filename = filename.strip()
    if not filename:
        raise ValueError("Filename cannot be empty or whitespace only")

    # Check for dangerous patterns that could indicate path traversal
    # This includes both Unix (..) and Windows (..\) style traversal
    dangerous_patterns = ["../", "..\\", "../", "..\\"]
    if any(pattern in filename for pattern in dangerous_patterns):
        raise ValueError("Filename contains invalid path traversal components")

    # Check for Windows drive letters (C:, D:, etc.)
    if len(filename) >= 2 and filename[1] == ":" and filename[0].isalpha():
        raise ValueError("Filename cannot contain Windows drive letters")

    # Create a path from the filename
    filename_path = Path(filename)

    # Check if it's an absolute path
    if filename_path.is_absolute():
        raise ValueError("Filename cannot be an absolute path")

    # Construct the full path within temp directory
    file_path = temp_dir / filename_path

    # Resolve both paths to check for path traversal
    resolved_file = await file_path.resolve()
    resolved_temp = await temp_dir.resolve()

    # Ensure the resolved file path is within the temp directory
    try:
        resolved_file.relative_to(resolved_temp)
    except ValueError:
        raise ValueError("Filename contains invalid path traversal components")

    return file_path
