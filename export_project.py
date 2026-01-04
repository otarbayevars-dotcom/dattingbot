import os
import sys

def export_project(root_dir, output_file, extensions=None):
    """
    Экспортирует содержимое проекта в текстовый файл
    
    Args:
        root_dir: Корневая директория проекта
        output_file: Выходной файл
        extensions: Список расширений для включения (None = все файлы)
    """
    excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
    excluded_files = {output_file}
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for root, dirs, files in os.walk(root_dir):
            # Пропускаем исключенные директории
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file in excluded_files:
                    continue
                    
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, root_dir)
                
                # Проверяем расширение файла
                if extensions:
                    if not any(file.endswith(ext) for ext in extensions):
                        continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    out.write("=" * 80 + "\n")
                    out.write(f"ФАЙЛ: {rel_path}\n")
                    out.write("=" * 80 + "\n\n")
                    out.write(content)
                    out.write("\n\n" + "=" * 80 + "\n\n")
                    
                except (UnicodeDecodeError, PermissionError):
                    # Пропускаем бинарные файлы и файлы без доступа
                    out.write("=" * 80 + "\n")
                    out.write(f"ФАЙЛ: {rel_path} (бинарный файл, содержимое не отображается)\n")
                    out.write("=" * 80 + "\n\n")
                    
        print(f"Проект экспортирован в {output_file}")

if __name__ == "__main__":
    # Настройки
    PROJECT_DIR = "."  # Текущая директория
    OUTPUT_FILE = "project_export.txt"
    
    # Можно указать конкретные расширения файлов
    INCLUDE_EXTENSIONS = [
        '.py', '.js', '.jsx', '.ts', '.tsx', 
        '.html', '.css', '.scss', '.json', 
        '.xml', '.yml', '.yaml', '.md',
        '.txt', '.csv', '.sql', '.java',
        '.cpp', '.c', '.h', '.php', '.rb',
        '.go', '.rs', '.swift', '.kt'
    ]
    
    export_project(PROJECT_DIR, OUTPUT_FILE, INCLUDE_EXTENSIONS)