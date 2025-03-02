import os
import shutil
from datetime import datetime
import argparse
from pathlib import Path
from PIL import Image
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    return logging.getLogger(__name__)

def get_image_creation_date(image_path):
    try:
        # Try to get EXIF data
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif is not None:
                # Look for DateTimeOriginal tag (36867)
                if 36867 in exif:
                    date_str = exif[36867]
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    
    # Fallback to file creation time
    stat = os.stat(image_path)
    return datetime.fromtimestamp(stat.st_mtime)

def create_year_month_folders(base_dir, date, skip_year=False):
    # Create month folder (MM)
    month_folder = date.strftime('%m')
    
    if skip_year:
        # If skip_year is True, create month folders directly in base_dir
        folder_path = os.path.join(base_dir, month_folder)
    else:
        # Create year folder (YYYY) and month subfolder
        year_folder = date.strftime('%Y')
        year_path = os.path.join(base_dir, year_folder)
        folder_path = os.path.join(year_path, month_folder)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def is_image_file(filename):
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    return os.path.splitext(filename.lower())[1] in image_extensions

def organize_photos(directory='.', skip_year=False):
    logger = setup_logging()
    logger.info(f"Starting photo organization in: {directory}")
    logger.info("Organizing by month only" if skip_year else "Organizing by year and month")
    
    # Convert to absolute path
    directory = os.path.abspath(directory)
    
    # Counter for statistics
    stats = {'processed': 0, 'skipped': 0, 'errors': 0}
    
    # Scan for image files
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip if it's a directory or not an image file
        if os.path.isdir(file_path) or not is_image_file(filename):
            stats['skipped'] += 1
            continue
        
        try:
            # Get creation date
            creation_date = get_image_creation_date(file_path)
            
            # Create month folder
            month_folder = create_year_month_folders(directory, creation_date, skip_year)
            
            # Construct destination path
            dest_path = os.path.join(month_folder, filename)
            
            # Handle duplicate filenames
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(month_folder, new_filename)
                    counter += 1
            
            # Move the file
            shutil.move(file_path, dest_path)
            logger.info(f"Moved: {filename} -> {creation_date.strftime('%m') if skip_year else creation_date.strftime('%Y/%m')}/")
            stats['processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            stats['errors'] += 1

    # Print summary
    logger.info("\nSummary:")
    logger.info(f"Processed: {stats['processed']} images")
    logger.info(f"Skipped: {stats['skipped']} files")
    logger.info(f"Errors: {stats['errors']} files")

def main():
    parser = argparse.ArgumentParser(description='Organize photos into year/month folders or month-only folders.')
    parser.add_argument('--directory', '-d', default='.',
                    help='Directory containing photos (default: current directory)')
    parser.add_argument('--no-year-folders', '-n', action='store_true',
                    help='Organize photos by month only, without creating year folders')
    args = parser.parse_args()

    organize_photos(args.directory, skip_year=args.no_year_folders)

if __name__ == '__main__':
    main()

