import os
import sys

try:
    import pathspec
except ImportError:
    print("The 'pathspec' module is required to run this script.")
    print("Please install it using 'pip install pathspec' and try again.")
    sys.exit(1)

def ensure_promptignore_contains(files):
    promptignore_path = '.promptignore'
    existing_entries = set()
    if os.path.exists(promptignore_path):
        with open(promptignore_path, 'r') as f:
            existing_entries = set(line.strip() for line in f if line.strip())
    with open(promptignore_path, 'a') as f:
        for file in files:
            if file not in existing_entries:
                f.write(file + '\n')
                existing_entries.add(file)

def load_ignore_patterns():
    default_ignore_patterns = [
        '.git/',
        '.hg/',
        '.svn/',
        '.bzr/',
        '.DS_Store',
        'Thumbs.db',
        'node_modules/',
        'env/',
        'venv/',
        '__pycache__/',
        '*.pyc',
        '.idea/',
        '.vscode/',
        '*.log',
        '*.tmp',
        '*.swp',
        '*.swo',
        'build/',
        'dist/',
        '*.egg-info/',
    ]

    ignore_patterns = default_ignore_patterns.copy()

    # Load patterns from .gitignore
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_lines = f.read().splitlines()
        ignore_patterns.extend(gitignore_lines)

    # Load patterns from .promptignore
    if os.path.exists('.promptignore'):
        with open('.promptignore', 'r') as f:
            promptignore_lines = f.read().splitlines()
        ignore_patterns.extend(promptignore_lines)

    spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
    return spec

def should_ignore(path, spec):
    if spec is None:
        return False
    # Remove leading './' from path for correct matching
    relative_path = os.path.relpath(path, '.')
    return spec.match_file(relative_path)

comment_syntax = {
    '.py': ('# ', ''),
    '.js': ('// ', ''),
    '.css': ('/* ', ' */'),
    '.html': ('<!-- ', ' -->'),
    '.htm': ('<!-- ', ' -->'),
    '.php': ('// ', ''),
    '.rb': ('# ', ''),
    '.dart': ('// ', ''),
    '.swift': ('// ', ''),
    '.java': ('// ', ''),
    '.c': ('// ', ''),
    '.cpp': ('// ', ''),
    '.h': ('// ', ''),
    '.cs': ('// ', ''),
    '.xml': ('<!-- ', ' -->'),
    '.kt': ('// ', ''),  # Kotlin
    '.go': ('// ', ''),
    '.scala': ('// ', ''),
    '.sh': ('# ', ''),
    '.bat': ('REM ', ''),
    '.pl': ('# ', ''),
    '.rs': ('// ', ''),  # Rust
    '.sql': ('-- ', ''),
    # Add more extensions as needed
}

# Extensions that require special handling (insert comments after the first line)
special_first_line_extensions = ['.php', '.sh', '.py', '.pl', '.rb']

def get_comment_syntax(filename):
    _, ext = os.path.splitext(filename)
    return comment_syntax.get(ext.lower(), ('# ', ''))

def has_shebang(line):
    return line.startswith('#!')

def display_file_list(files, added_files, removed_files):
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    print("\nFiles with comments:")
    for idx, file_info in enumerate(files, start=1):
        # Update line count before displaying
        try:
            with open(file_info['filepath'], 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            file_info['line_count'] = len(lines)
        except Exception as e:
            print(f"Error reading file '{file_info['filepath']}': {e}")
            continue
        status_tag = ''
        if file_info['filepath'] in added_files:
            status_tag = f" {GREEN}(added){RESET}"
        elif file_info['filepath'] in removed_files:
            status_tag = f" {RED}(removed){RESET}"
        print(f"{idx}. {file_info['filepath']} (lines: {file_info['line_count']}){status_tag}")

def generate_files_prompt(files_with_comments):
    added_files = set()
    removed_files = set()
    # Load previously added files from a tracking file
    tracking_filename = '.files_added_list'
    if os.path.exists(tracking_filename):
        with open(tracking_filename, 'r') as f:
            added_files = set(line.strip() for line in f if line.strip())

    prompt_filename = 'prompt-files.txt'

    while True:
        display_file_list(files_with_comments, added_files, removed_files)
        # Get the current number of lines in prompt-files.txt
        if os.path.exists(prompt_filename):
            with open(prompt_filename, 'r', encoding='utf-8', errors='ignore') as f_prompt:
                prompt_lines = f_prompt.readlines()
            line_count = len(prompt_lines)
        else:
            line_count = 0
        print(f"\nCurrent number of lines in '{prompt_filename}': {line_count}")
        print("\nEnter the number of the file to toggle (add/remove) in 'prompt-files.txt', 'r' to refresh, 's' to start over, or 'x' to exit:")
        user_input = input("> ").strip()
        if user_input.lower() == 'x':
            break
        elif user_input.lower() == 'r':
            # Refresh the prompt-files.txt with updated content of added files
            if added_files:
                with open(prompt_filename, 'w', encoding='utf-8', errors='ignore') as f_out:
                    for file_path in added_files:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_in:
                                content = f_in.read()
                                f_out.write(content)
                        except Exception as e:
                            print(f"Error reading file '{file_path}': {e}")
                print(f"\nRefreshed '{prompt_filename}' with updated content of added files.")
            else:
                print("\nNo files have been added yet to refresh.")
        elif user_input.lower() == 's':
            # Start over: clear prompt-files.txt and reset added files
            open(prompt_filename, 'w').close()  # Clear the file
            added_files.clear()
            removed_files.clear()
            # Clear tracking file
            open(tracking_filename, 'w').close()
            print(f"\n'{prompt_filename}' has been cleared. You can start adding files again.")
        else:
            try:
                selection = int(user_input)
                if 1 <= selection <= len(files_with_comments):
                    file_info = files_with_comments[selection - 1]
                    file_path = file_info['filepath']
                    if file_path in added_files:
                        # Remove the file from added_files
                        added_files.remove(file_path)
                        removed_files.add(file_path)
                        # Update tracking file
                        with open(tracking_filename, 'w') as f_tracking:
                            for path in added_files:
                                f_tracking.write(path + '\n')
                        # Regenerate prompt-files.txt
                        if added_files:
                            with open(prompt_filename, 'w', encoding='utf-8', errors='ignore') as f_out:
                                for path in added_files:
                                    try:
                                        with open(path, 'r', encoding='utf-8', errors='ignore') as f_in:
                                            content = f_in.read()
                                            f_out.write(content)
                                    except Exception as e:
                                        print(f"Error reading file '{path}': {e}")
                        else:
                            # Clear the file if no files are added
                            open(prompt_filename, 'w').close()
                        print(f"\nRemoved '{file_path}' from '{prompt_filename}'.")
                    else:
                        # Add the file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_in:
                                content = f_in.read()
                            with open(prompt_filename, 'a', encoding='utf-8', errors='ignore') as f_out:
                                f_out.write(content)
                            # Update added_files
                            added_files.add(file_path)
                            if file_path in removed_files:
                                removed_files.remove(file_path)
                            # Update tracking file
                            with open(tracking_filename, 'w') as f_tracking:
                                for path in added_files:
                                    f_tracking.write(path + '\n')
                            print(f"\nAppended '{file_path}' to '{prompt_filename}'.")
                        except Exception as e:
                            print(f"Error processing file '{file_path}': {e}")
                else:
                    print("\nInvalid selection. Please enter a valid number.")
            except ValueError:
                print("\nInvalid input. Please enter a number, 'r' to refresh, 's' to start over, or 'x' to exit.")

def main():
    spec = load_ignore_patterns()

    # Ensure the script itself and prompt-files.txt are added to .promptignore
    script_path = os.path.abspath(sys.argv[0])
    script_relative_path = os.path.relpath(script_path, '.')
    prompt_filename = 'prompt-files.txt'
    ensure_promptignore_contains([script_relative_path, prompt_filename])

    files_with_comments = []
    files_without_comments = []

    for root, dirs, files in os.walk('.'):
        # Exclude hidden directories and those that should be ignored
        dirs[:] = [d for d in dirs if not (d.startswith('.') or should_ignore(os.path.join(root, d), spec))]
        for file in files:
            if file.startswith('.'):
                continue  # Skip hidden files
            filepath = os.path.join(root, file)
            if should_ignore(filepath, spec):
                continue
            # Read the first and last lines (adjusted for special cases)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                if not lines:
                    continue  # Empty file

                # Determine where to look for 'file start' comment
                first_line = lines[0].strip()
                filename = os.path.basename(filepath)
                _, ext = os.path.splitext(filename)
                needs_special_handling = ext.lower() in special_first_line_extensions

                # For files with shebang lines, adjust the first line
                if has_shebang(first_line) or (ext.lower() == '.php' and first_line.startswith('<?php')):
                    comment_line_index = 1
                else:
                    comment_line_index = 0

                # Check for 'file start' and 'file end' comments
                if len(lines) > comment_line_index:
                    possible_comment_line = lines[comment_line_index].strip()
                else:
                    possible_comment_line = ''

                last_line = lines[-1].strip()

                # Include '(do not remove)' in the search
                file_start_indicator = 'file start'
                file_end_indicator = 'file end'
                if 'do not remove' not in possible_comment_line.lower():
                    possible_comment_line = ''
                if 'do not remove' not in last_line.lower():
                    last_line = ''

                file_info = {
                    'filepath': filepath,
                    'line_count': len(lines),
                }

                if (file_start_indicator in possible_comment_line and file_end_indicator in last_line):
                    files_with_comments.append(file_info)
                else:
                    files_without_comments.append(file_info)
            except Exception as e:
                print(f"Error processing file '{filepath}': {e}")
                continue

    if files_without_comments:
        # List files that need comments
        print("\nThe following files are missing comments:")
        for idx, file_info in enumerate(files_without_comments, start=1):
            print(f"{idx}. {file_info['filepath']}")

        choice = input(f"\nDo you want to add comments to these {len(files_without_comments)} files? (y/n): ").lower()
        files_failed_to_add_comments = []
        if choice == 'y':
            for file_info in files_without_comments:
                filepath = file_info['filepath']
                filename = os.path.basename(filepath)
                comment_start, comment_end = get_comment_syntax(filename)
                file_start_comment = f"{comment_start}file start: {filepath} (do not remove){comment_end}"
                file_end_comment = f"{comment_start}file end: {filepath} (do not remove){comment_end}"
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    if not lines:
                        continue  # Empty file

                    first_line = lines[0].strip()
                    _, ext = os.path.splitext(filename)
                    needs_special_handling = ext.lower() in special_first_line_extensions

                    insert_index = 0
                    # Adjust insertion index for shebang or PHP opening tag
                    if has_shebang(first_line) or (ext.lower() == '.php' and first_line.startswith('<?php')):
                        insert_index = 1

                    # Insert the 'file start' comment after the first line if needed
                    lines.insert(insert_index, file_start_comment + '\n')
                    lines.append('\n' + file_end_comment + '\n')

                    with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                        f.writelines(lines)
                    # Update the files_with_comments list
                    file_info['line_count'] = len(lines)
                    files_with_comments.append(file_info)
                except Exception as e:
                    print(f"Error updating file '{filepath}': {e}")
                    files_failed_to_add_comments.append(filepath)
            files_without_comments = []  # All files have been processed
        else:
            files_failed_to_add_comments = [file_info['filepath'] for file_info in files_without_comments]

        # After attempting to add comments, ask about .promptignore
        if files_failed_to_add_comments:
            print("\nThe following files did not have comments added:")
            for filepath in files_failed_to_add_comments:
                print(f"- {filepath}")

            choice = input("\nWould you like to add these files to '.promptignore'? (y/n): ").lower()
            if choice == 'y':
                ensure_promptignore_contains(files_failed_to_add_comments)
                print("Files have been added to '.promptignore'.")

    if files_with_comments:
        generate_files_prompt(files_with_comments)
    else:
        print("\nNo files with comments were found.")

if __name__ == "__main__":
    main()
