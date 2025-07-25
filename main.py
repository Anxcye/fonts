import os
import json
# import shutil
from PIL import Image, ImageDraw, ImageFont
import sys
# import glob

# Configuration
FONTS_DIR = "." # The base directory containing font folders
MANIFEST_PATH = "fonts-manifest.json"
PREVIEW_TEXT = "草草杯盘共笑语，昏昏灯火话平生。 \nABCDEFGHIJK,abcdefghijk.\n 1234567890"
PREVIEW_SIZE = (800, 200)
FONT_SIZE = 48
PREVIEW_BG = (255, 255, 255, 0)  # Transparent background
PREVIEW_FG = (0, 0, 0, 255)  # Black text

def load_manifest():
    """Load the font manifest JSON file."""
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file '{MANIFEST_PATH}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Manifest file '{MANIFEST_PATH}' contains invalid JSON.")
        sys.exit(1)

def get_all_font_files():
    """Get a list of all font files in the directories."""
    all_font_files = []
    for root, _, files in os.walk(FONTS_DIR):
        for file in files:
            if file.lower().endswith(('.ttf', '.otf')):
                # Get path relative to FONTS_DIR
                rel_path = os.path.relpath(os.path.join(root, file), FONTS_DIR)
                all_font_files.append(rel_path)
    return all_font_files

def get_manifest_font_files(manifest):
    """Extract all font files listed in the manifest."""
    manifest_files = []
    for font in manifest:
        if "files" in font:
            manifest_files.extend(font["files"])
    return manifest_files

def find_orphaned_font_files():
    """Find font files that are not in the manifest."""
    manifest = load_manifest()
    manifest_files = get_manifest_font_files(manifest)
    all_files = get_all_font_files()
    
    orphaned_files = [f for f in all_files if f not in manifest_files]
    return orphaned_files

def delete_orphaned_files():
    """List and delete orphaned font files after confirmation."""
    orphaned_files = find_orphaned_font_files()
    
    if not orphaned_files:
        print("No orphaned font files found.")
        return
    
    print("\nFound the following orphaned font files:")
    for i, file in enumerate(orphaned_files, 1):
        print(f"{i}. {file}")
    
    confirm = input("\nDo you want to delete these files? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    for file in orphaned_files:
        full_path = os.path.join(FONTS_DIR, file)
        try:
            os.remove(full_path)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")
    
    print(f"\nDeleted {len(orphaned_files)} orphaned font files.")

def create_preview_image(font_path, output_path, text=PREVIEW_TEXT):
    """Create a preview image for the specified font."""
    try:
        # Create a transparent image
        img = Image.new('RGBA', PREVIEW_SIZE, PREVIEW_BG)
        draw = ImageDraw.Draw(img)
        
        # Load the font
        font = ImageFont.truetype(font_path, FONT_SIZE)
        
        # Split text into lines and calculate dimensions for each line
        lines = text.split('\n')
        line_heights = []
        line_widths = []
        
        for line in lines:
            try:
                # Try newer Pillow method first
                bbox = font.getbbox(line)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                line_widths.append(width)
                line_heights.append(height)
            except AttributeError:
                try:
                    # Fall back to older method
                    width, height = draw.textsize(line, font=font)
                    line_widths.append(width)
                    line_heights.append(height)
                except Exception:
                    # If both methods fail, use a different approach
                    width = sum(font.getlength(char) for char in line)
                    # Approximate height based on font size
                    height = int(FONT_SIZE * 1.2)
                    line_widths.append(width)
                    line_heights.append(height)
        
        # Calculate total text height and max width
        total_height = sum(line_heights) + (len(lines) - 1) * int(FONT_SIZE * 0.3)
        max_width = max(line_widths) if line_widths else 0
        
        # Calculate starting position
        start_x = (PREVIEW_SIZE[0] - max_width) // 2
        start_y = (PREVIEW_SIZE[1] - total_height) // 2
        
        # Draw each line of text
        current_y = start_y
        for i, line in enumerate(lines):
            x_pos = (PREVIEW_SIZE[0] - line_widths[i]) // 2
            draw.text((x_pos, current_y), line, font=font, fill=PREVIEW_FG)
            current_y += line_heights[i] + int(FONT_SIZE * 0.3)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the image
        img.save(output_path, 'PNG')
        print(f"Preview created: {output_path}")
        return True
    except Exception as e:
        print(f"Error creating preview for {font_path}: {e}")
        return False

def create_font_previews():
    """Create preview images for fonts specified in the manifest."""
    manifest = load_manifest()
    
    # Get font selection from user
    print("\nCreate font preview images:")
    print("1. Generate preview for a specific font")
    print("2. Generate previews for all fonts")
    print("3. Generate missing previews only")
    choice = input("Select an option (1-3): ").strip()
    
    if choice == '1':
        # Show font list
        print("\nAvailable fonts:")
        for i, font in enumerate(manifest, 1):
            if "name" in font:
                print(f"{i}. {font.get('name', 'Unnamed Font')}")
        
        try:
            idx = int(input("\nEnter font number: ").strip()) - 1
            if 0 <= idx < len(manifest):
                process_single_font(manifest[idx])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    elif choice == '2':
        # Process all fonts
        for font in manifest:
            process_single_font(font)
    
    elif choice == '3':
        # Process only fonts without previews
        for font in manifest:
            if "preview" in font and os.path.exists(os.path.join(FONTS_DIR, font["preview"])):
                continue
            process_single_font(font)
    
    else:
        print("Invalid option.")

def process_single_font(font_data):
    """Process a single font entry to create its preview."""
    if "id" not in font_data or "files" not in font_data or not font_data["files"]:
        print(f"Skipping font with missing id or files: {font_data.get('name', 'unknown')}")
        return
    
    font_id = font_data["id"]
    font_file = font_data["files"][0]  # Use the first font file
    
    # Determine preview file path
    if "preview" in font_data:
        preview_path = os.path.join(FONTS_DIR, font_data["preview"])
    else:
        # Create a default preview path if not specified
        preview_dir = os.path.join(os.path.dirname(font_file), "preview.png")
        preview_path = os.path.join(FONTS_DIR, preview_dir)
    
    # Create the preview
    font_path = os.path.join(FONTS_DIR, font_file)
    if os.path.exists(font_path):
        create_preview_image(font_path, preview_path)
    else:
        print(f"Font file not found: {font_path}")

def verify_font_files():
    """Check if all font files in the manifest exist and if all font IDs have previews."""
    manifest = load_manifest()
    
    missing_files = []
    missing_previews = []
    duplicate_ids = set()
    seen_ids = set()
    
    # Get manifest font files
    manifest_files = get_manifest_font_files(manifest)
    
    # Check each font entry in the manifest
    for font in manifest:
        # Check for duplicate IDs
        if "id" in font:
            if font["id"] in seen_ids:
                duplicate_ids.add(font["id"])
            seen_ids.add(font["id"])
        else:
            print(f"Warning: Font entry missing ID: {font.get('name', 'Unnamed Font')}")
        
        # Check if font files exist
        if "files" in font:
            for file in font["files"]:
                file_path = os.path.join(FONTS_DIR, file)
                if not os.path.exists(file_path):
                    missing_files.append((font.get("id", "unknown"), file))
        else:
            print(f"Warning: Font entry has no files: {font.get('id', 'unknown')}")
        
        # Check if preview exists
        if "preview" in font:
            preview_path = os.path.join(FONTS_DIR, font["preview"])
            if not os.path.exists(preview_path):
                missing_previews.append((font.get("id", "unknown"), font["preview"]))
        else:
            missing_previews.append((font.get("id", "unknown"), "No preview specified"))
    
    # Find orphaned font files (exist but not in manifest)
    orphaned_files = find_orphaned_font_files()
    
    # Print results
    if not missing_files and not missing_previews and not duplicate_ids and not orphaned_files:
        print("\nAll font files and previews are present. No duplicate IDs found. No orphaned files.")
    else:
        if missing_files:
            print("\nMissing font files:")
            for font_id, file in missing_files:
                print(f"  Font ID: {font_id}, Missing file: {file}")
        
        if missing_previews:
            print("\nMissing preview images:")
            for font_id, preview in missing_previews:
                print(f"  Font ID: {font_id}, Missing preview: {preview}")
        
        if duplicate_ids:
            print("\nDuplicate font IDs:")
            for font_id in duplicate_ids:
                print(f"  Duplicate ID: {font_id}")
        
        if orphaned_files:
            print("\nOrphaned font files (exist but not in manifest):")
            for i, file in enumerate(orphaned_files, 1):
                print(f"  {i}. {file}")
            
            # Ask if user wants to delete orphaned files
            confirm = input("\nDo you want to delete these orphaned files? (y/n): ").strip().lower()
            if confirm == 'y':
                deleted_count = 0
                for file in orphaned_files:
                    full_path = os.path.join(FONTS_DIR, file)
                    try:
                        os.remove(full_path)
                        print(f"Deleted: {file}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {file}: {e}")
                
                print(f"\nDeleted {deleted_count} out of {len(orphaned_files)} orphaned font files.")
            else:
                print("Orphaned files not deleted.") 
def reduce_large_font_files():
    """Find font files larger than 24.5MiB and reduce their size using subsetting."""
    import subprocess
    from pathlib import Path
    
    SIZE_LIMIT = 24.5 * 1024 * 1024  # 24.5 MiB in bytes
    SUBSET_FILE = "./subset.txt"
    
    # Load subset characters
    try:
        with open(SUBSET_FILE, 'r', encoding='utf-8') as f:
            subset_chars = f.read()
        print(f"Loaded {len(subset_chars)} characters from subset file.")
    except FileNotFoundError:
        print(f"Error: Subset file '{SUBSET_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading subset file: {e}")
        return
    
    # Check if fonttools is installed
    try:
        subprocess.run(['pyftsubset', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: 'pyftsubset' not found. Please install fonttools:")
        print("pip install fonttools")
        return
    
    # Load manifest to get font files
    manifest = load_manifest()
    all_font_files = []
    for font in manifest:
        if "files" in font and font["files"]:
            for file in font["files"]:
                all_font_files.append((font.get("id", "unknown"), file))
    
    # Find large font files
    large_files = []
    for font_id, file in all_font_files:
        file_path = Path(FONTS_DIR) / file
        if file_path.exists():
            size = file_path.stat().st_size
            if size > SIZE_LIMIT:
                large_files.append((font_id, file, size))
    
    if not large_files:
        print("No font files larger than 24.5MiB found.")
        return
    
    # Display large files
    print(f"\nFound {len(large_files)} font files larger than 24.5MiB:")
    for i, (font_id, file, size) in enumerate(large_files, 1):
        print(f"{i}. Font ID: {font_id}, File: {file}, Size: {size/1024/1024:.2f} MiB")
    
    confirm = input("\nDo you want to reduce these files by subsetting? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Process each large file
    results = []
    still_large = []
    
    for font_id, file, original_size in large_files:
        file_path = Path(FONTS_DIR) / file
        output_dir = file_path.parent
        output_file = output_dir / f"{file_path.stem}.subset{file_path.suffix}"
        
        print(f"\nProcessing {file}...")
        
        # Create subset command
        cmd = [
            'pyftsubset', 
            str(file_path),
            f'--text={subset_chars}',
            '--layout-features=*',
            f'--output-file={output_file}'
        ]
        
        try:
            # Run subsetting command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Check if output file exists and get its size
            if output_file.exists():
                new_size = output_file.stat().st_size
                
                # Check if we should replace the original
                if new_size < original_size:
                    # Backup original
                    backup_file = output_dir / f"{file_path.stem}.original{file_path.suffix}"
                    file_path.rename(backup_file)
                    
                    # Move subset to original name
                    output_file.rename(file_path)
                    
                    results.append((font_id, file, original_size, new_size))
                    
                    # Check if still over limit
                    if new_size > SIZE_LIMIT:
                        still_large.append((font_id, file, new_size))
                else:
                    print(f"  Subset not smaller than original, keeping original.")
                    output_file.unlink()  # Delete the output file
            else:
                print(f"  Error: Output file not created.")
        
        except Exception as e:
            print(f"  Error processing {file}: {e}")
    
    # Print results
    if results:
        print("\nSubsetting Results:")
        print("------------------------------------------------------------")
        print("Font ID                 | Original Size | New Size | Reduction")
        print("------------------------------------------------------------")
        for font_id, file, original, new in results:
            reduction = (1 - new/original) * 100
            print(f"{font_id:<24} | {original/1024/1024:11.2f} MiB | {new/1024/1024:8.2f} MiB | {reduction:8.2f}%")
    
    if still_large:
        print("\nFonts still larger than 24.5MiB after subsetting:")
        for font_id, file, size in still_large:
            print(f"  Font ID: {font_id}, File: {file}, Size: {size/1024/1024:.2f} MiB")
    
    print("\nFont reduction completed.")

def update_file_size_info():
    """Update the manifest JSON with file size information for each font."""
    manifest = load_manifest()
    updated_count = 0
    
    print("\nUpdating font file size information in manifest...")
    
    for font in manifest:
        if "files" in font and font["files"]:
            total_size = 0
            for file in font["files"]:
                file_path = os.path.join(FONTS_DIR, file)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    total_size += size
            
            # Update or add the size field
            old_size = font.get("size", None)
            font["size"] = total_size
            
            # Determine if this was an update or an addition
            if old_size is None:
                print(f"Added size: {font.get('id', 'unknown')} - {total_size/1024/1024:.2f} MiB")
            elif old_size != total_size:
                print(f"Updated size: {font.get('id', 'unknown')} - {old_size/1024/1024:.2f} MiB → {total_size/1024/1024:.2f} MiB")
            
            updated_count += 1
    
    # Save the updated manifest
    try:
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"\nUpdated size information for {updated_count} fonts and saved to {MANIFEST_PATH}")
        return True
    except Exception as e:
        print(f"Error saving manifest: {e}")
        return False

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        print("\n==== Font Management Tool ====")
        print("1. List and delete orphaned font files")
        print("2. Create font preview images")
        print("3. Verify font files and manifests")
        print("4. Reduce large font files (>24.5MiB)")
        print("5. Update font file size information in manifest")
        print("6. Exit")
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            delete_orphaned_files()
        elif choice == '2':
            create_font_previews()
        elif choice == '3':
            verify_font_files()
        elif choice == '4':
            reduce_large_font_files()
        elif choice == '5':
            update_file_size_info()
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu()