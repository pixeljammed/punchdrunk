import os
import mimetypes
from pathlib import Path

def detect_file_type(file_path):
    """Detect actual file type by reading file signature (magic bytes)"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(32)  # Read more bytes for better detection

        # Check GIF signature
        if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return 'gif'

        # Check HTML/text files (some gifs are actually HTML pages)
        if header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
            return 'html'

        # Check for "This content is no longer available" text files
        if header.startswith(b'This content is no longer'):
            return 'text_error'

        # Check for generic text/Python files
        if header.startswith(b'import ') or header.startswith(b'#!/usr/bin') or header.startswith(b'# '):
            return 'text_file'

        # Check MP4/video signatures
        if len(header) >= 8 and header[4:8] == b'ftyp':  # MP4, M4V, etc.
            return 'mp4'

        # Check WebM
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return 'webm'

        # Check AVI
        if header.startswith(b'RIFF') and len(header) >= 12 and header[8:12] == b'AVI ':
            return 'avi'

        # Check MOV (QuickTime) - need to read more
        with open(file_path, 'rb') as f:
            chunk = f.read(256)
            if b'moov' in chunk or b'mdat' in chunk or (b'ftyp' in chunk and b'qt' in chunk):
                return 'mov'

        # Check PNG
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'

        # Check JPEG
        if header.startswith(b'\xff\xd8\xff'):
            return 'jpeg'

        # Check WEBP
        if header.startswith(b'RIFF') and len(header) >= 12 and header[8:12] == b'WEBP':
            return 'webp'

        # Check APNG (animated PNG)
        if header.startswith(b'\x89PNG'):
            with open(file_path, 'rb') as f:
                content = f.read(1024)
                if b'acTL' in content:  # Animation control chunk
                    return 'apng'

        # Unknown file type - show debug info
        print(f"? Unknown file type: {os.path.basename(file_path)}")
        print(f"  First 32 bytes (hex): {header.hex()}")
        print(f"  First 32 bytes (text): {repr(header)}")

        return 'unknown'
    except Exception as e:
        print(f"✗ Error reading file {file_path}: {e}")
        return None

def clean_filename(filename):
    """Clean up filename by removing all extensions"""
    name = filename
    while True:
        name_part, ext = os.path.splitext(name)
        if ext:
            name = name_part
        else:
            break
    return name

def convert_to_gif(input_path, output_path):
    """Convert video to GIF using ffmpeg"""
    # Use a temp file if input and output are the same
    temp_output = None
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        temp_output = str(output_path) + ".tmp.gif"
        actual_output = temp_output
    else:
        actual_output = output_path

    cmd = f'ffmpeg -i "{input_path}" -vf "fps=15,scale=480:-1:flags=lanczos" -y "{actual_output}"'
    print(f"Converting: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    result = os.system(cmd)

    # If we used a temp file, replace the original
    if temp_output and result == 0:
        try:
            os.replace(temp_output, output_path)
        except Exception as e:
            print(f"Error replacing file: {e}")
            return 1

    return result

def process_folder(folder_path):
    """Process all video files and GIFs in the folder"""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return

    # Get all files (not directories)
    files = [f for f in folder.iterdir() if f.is_file()]

    if not files:
        print("No files found in folder")
        return

    processed = []
    html_files = []
    text_error_files = []
    text_files = []
    unknown_files = []
    stats = {'converted': 0, 'renamed': 0, 'skipped': 0, 'failed': 0}

    print(f"Found {len(files)} files to process...\n")

    for file in files:
        file_type = detect_file_type(file)

        if not file_type:
            stats['skipped'] += 1
            continue

        # Track HTML files separately
        if file_type == 'html':
            html_files.append(file)
            stats['skipped'] += 1
            continue

        # Track "content no longer available" error files
        if file_type == 'text_error':
            text_error_files.append(file)
            stats['skipped'] += 1
            continue

        # Track other text files (like Python scripts)
        if file_type == 'text_file':
            text_files.append(file)
            stats['skipped'] += 1
            continue

        # Track unknown files
        if file_type == 'unknown':
            unknown_files.append(file)
            stats['skipped'] += 1
            continue

        # Clean the filename
        clean_name = clean_filename(file.name)
        new_filename = f"{clean_name}.gif"

        # Handle potential name conflicts
        counter = 1
        final_name = new_filename
        output_path = folder / final_name

        while output_path.exists() and output_path != file:
            final_name = f"{clean_name}_{counter}.gif"
            output_path = folder / final_name
            counter += 1

        # Process based on actual file type
        if file_type == 'gif':
            # Already a GIF, just rename if needed
            if file.name != final_name:
                try:
                    file.rename(output_path)
                    print(f"✓ Renamed GIF: {file.name} -> {final_name}")
                    stats['renamed'] += 1
                except Exception as e:
                    print(f"✗ Failed to rename {file.name}: {e}")
                    stats['failed'] += 1
            else:
                print(f"• Already correct: {file.name}")
                stats['skipped'] += 1

        elif file_type in ['mp4', 'webm', 'avi', 'mov']:
            # Convert video to GIF
            result = convert_to_gif(str(file), str(output_path))
            if result == 0:
                print(f"✓ Converted {file_type.upper()}: {file.name} -> {final_name}")
                # Only delete if input and output were different files
                if file != output_path:
                    try:
                        file.unlink()  # Delete original video
                    except Exception as e:
                        print(f"Warning: Couldn't delete original file: {e}")
                stats['converted'] += 1
            else:
                print(f"✗ Failed to convert: {file.name}")
                stats['failed'] += 1

        elif file_type in ['png', 'jpeg', 'webp', 'apng']:
            # Static images or animated formats - try to convert with ffmpeg
            result = convert_to_gif(str(file), str(output_path))
            if result == 0:
                print(f"✓ Converted {file_type.upper()}: {file.name} -> {final_name}")
                if file != output_path:
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Warning: Couldn't delete original file: {e}")
                stats['converted'] += 1
            else:
                print(f"✗ Failed to convert {file_type.upper()}: {file.name}")
                stats['failed'] += 1

        processed.append(output_path)

    # Print summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Converted: {stats['converted']}")
    print(f"  Renamed: {stats['renamed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    print("="*50)

    # Handle HTML files
    if html_files:
        print(f"\n⚠ Found {len(html_files)} HTML files disguised as media:")
        for html_file in html_files:
            print(f"  - {html_file.name}")

        delete = input("\nDelete these HTML files? (y/n): ")
        if delete.lower() == 'y':
            deleted = 0
            for html_file in html_files:
                try:
                    html_file.unlink()
                    deleted += 1
                    print(f"✓ Deleted: {html_file.name}")
                except Exception as e:
                    print(f"✗ Failed to delete {html_file.name}: {e}")
            print(f"\nDeleted {deleted}/{len(html_files)} HTML files")
        else:
            print("HTML files kept.")

    # Handle "content no longer available" error files
    if text_error_files:
        print(f"\n⚠ Found {len(text_error_files)} failed download files (\"This content is no longer available\"):")
        for err_file in text_error_files:
            print(f"  - {err_file.name}")

        delete = input("\nDelete these error files? (y/n): ")
        if delete.lower() == 'y':
            deleted = 0
            for err_file in text_error_files:
                try:
                    err_file.unlink()
                    deleted += 1
                    print(f"✓ Deleted: {err_file.name}")
                except Exception as e:
                    print(f"✗ Failed to delete {err_file.name}: {e}")
            print(f"\nDeleted {deleted}/{len(text_error_files)} error files")
        else:
            print("Error files kept.")

    # Handle other text files
    if text_files:
        print(f"\n⚠ Found {len(text_files)} text/script files in the folder:")
        for txt_file in text_files:
            print(f"  - {txt_file.name}")
        print("\nThese are not media files and were skipped.")

    # Show unknown files
    if unknown_files:
        print(f"\n⚠ Found {len(unknown_files)} files with unknown format:")
        for unk_file in unknown_files:
            print(f"  - {unk_file.name}")
        print("\nThese files couldn't be identified. Check the debug output above for details.")

if __name__ == "__main__":
    folder_path = input("Enter the folder path: ").strip()

    # Remove quotes if user pastes path with quotes
    folder_path = folder_path.strip('"').strip("'")

    print(f"\nProcessing folder: {folder_path}\n")
    print("Note: This script requires ffmpeg for video conversion")
    print("Install: https://ffmpeg.org/download.html\n")

    confirm = input("This will convert all videos to GIF and fix filenames. Continue? (y/n): ")
    if confirm.lower() == 'y':
        print()
        process_folder(folder_path)
        print("\n✓ Done!")
    else:
        print("Cancelled.")