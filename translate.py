import json
import re
from pathlib import Path
from json import JSONDecodeError 
from tqdm import tqdm
from googletrans import Translator
import asyncio
import nbtlib
from nbtlib import parse_nbt

translator = Translator()

chinese_char_regex = re.compile(r'[\u4e00-\u9fff]+')

translation_cache = {}
files_translated = 0
strings_translated = 0

# Batch translation with retry
def translate_batch_with_retry(texts, max_retries=5):
    for attempt in range(max_retries):
        try:
            results = [translator.translate(t, dest="en").text for t in texts]
            return results
        except Exception as e:
            print(f"⚠️ Translation failed (attempt {attempt+1}): {e}")
    return texts

def batch_translate_texts(texts):
    batch_size = 100
    translated_results = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Translating batches"):
        batch = texts[i:i + batch_size]
        translated_batch = translate_batch_with_retry(batch)
        translated_results.extend(translated_batch)
    return translated_results

def translate_snbt_strings(snbt_string):
    try:
        nbt_data = parse_nbt(snbt_string)
    except Exception:
        return snbt_string  # Not valid SNBT

    def recursive_translate(nbt):
        if isinstance(nbt, nbtlib.Compound):
            for key in nbt:
                val = nbt[key]
                if isinstance(val, nbtlib.String):
                    if chinese_char_regex.search(val):
                        original = str(val)
                        if original in translation_cache:
                            nbt[key] = nbtlib.String(translation_cache[original])
                else:
                    recursive_translate(val)
        elif isinstance(nbt, list):
            for i in range(len(nbt)):
                if isinstance(nbt[i], nbtlib.String):
                    original = str(nbt[i])
                    if chinese_char_regex.search(original) and original in translation_cache:
                        nbt[i] = nbtlib.String(translation_cache[original])
                else:
                    recursive_translate(nbt[i])

    recursive_translate(nbt_data)
    return str(nbt_data)

# Step 1: Collect all Chinese texts
def collect_all_chinese_texts(folder):
    folder_path = Path(folder)
    quest_files = list(folder_path.rglob('*.*'))
    
    chinese_texts = set()

    def extract_chinese_strings(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                extract_chinese_strings(v)
        elif isinstance(obj, list):
            for i in obj:
                extract_chinese_strings(i)
        elif isinstance(obj, str):
            if chinese_char_regex.search(obj):
                chinese_texts.add(obj)

    quoted_string_regex = re.compile(r'"([^"]*[\u4e00-\u9fff][^"]*)"')

    def extract_chinese_from_text(text):
        matches = quoted_string_regex.findall(text)
        for match in matches:
            chinese_texts.add(match)

    for file_path in quest_files:
        parts = set(map(str.lower, file_path.parts))
        if 'quests' in parts or 'quest' in file_path.name.lower():
            try:
                if file_path.suffix == '.json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    extract_chinese_strings(data)
                elif file_path.suffix == '.snbt':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    extract_chinese_from_text(text)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")

    return list(chinese_texts)

# Step 2: Translate all unique texts
def translate_all_texts(texts):
    print(f"Translating {len(texts)} unique strings in batches...")
    translations = batch_translate_texts(texts)
    for original, translated in zip(texts, translations):
        translation_cache[original] = translated

# Step 3: Rewrite files
def translate_json_values(obj):
    global strings_translated
    if isinstance(obj, dict):
        return {k: translate_json_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [translate_json_values(i) for i in obj]
    elif isinstance(obj, str):
        if obj in translation_cache:
            strings_translated += 1
            return translation_cache[obj]
        else:
            return obj
    else:
        return obj

async def process_file(file_path):
    global files_translated, strings_translated
    try:
        # Plain text (cfg, zs, snbt, etc.)
        if file_path.suffix in ['.cfg', '.zs', '.kubejs', '.txt', '.mcfunction', '.snbt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            changed = False
            for line in lines:
                matches = chinese_char_regex.findall(line)
                if matches:
                    for chinese_text in matches:
                        if chinese_text in translation_cache:
                            line = line.replace(chinese_text, translation_cache[chinese_text])
                            strings_translated += 1
                            changed = True
                            print(f"Replacing '{chinese_text}' → '{translation_cache[chinese_text]}' in {file_path}")
                        else:
                            transl = translator.translate(chinese_text, dest='en')
                            translated_text = transl.text
                            translation_cache[chinese_text] = translated_text
                            line = line.replace(chinese_text, translated_text)
                            strings_translated += 1
                            changed = True
                            print(f"Translating '{chinese_text}' → '{translated_text}' in {file_path}")
                new_lines.append(line)

            if changed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"✅ Translated (Text) {file_path}")
                files_translated += 1
            return

        # JSON files
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            translated_data = translate_json_values(data)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Translated (JSON) {file_path}")
            files_translated += 1
            return

    except JSONDecodeError as e:
        print(f"⚠️ Skipped (invalid JSON): {file_path}: {e}")
    except Exception as e:
        print(f"❌ Failed to process {file_path}: {e}")

async def main(folder):
    # Step 1
    all_texts = collect_all_chinese_texts(folder)

    # Step 2
    translate_all_texts(all_texts)

    # Step 3
    folder_path = Path(folder)
    config_files = []
    for ext in ('*.json', '*.toml', '*.cfg', '*.snbt'):
        config_files.extend(folder_path.rglob(ext))

    for file_path in tqdm(config_files, desc="Processing files"):
        await process_file(file_path)

    print("\n===== SUMMARY =====")
    print(f"Files translated: {files_translated}")
    print(f"Strings translated: {strings_translated}")
    print("===================")
    print("✅ All files processed!")

if __name__ == "__main__":
    modpack_folder = r"C:\Users\Nojus\curseforge\minecraft\Instances\GregTech Quantum Transition"
    asyncio.run(main(modpack_folder))
