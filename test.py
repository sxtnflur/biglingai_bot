# grammar_corrector.py

import language_tool_python
import openai
import os

JAVA_PATH = r'C:\Users\Пользователь\Desktop\музик\openjdk-24+36_windows-x64_bin\jdk-24'
os.environ["JAVA_HOME"] = JAVA_PATH
os.environ["PATH"] = os.path.join(JAVA_PATH, "bin") + os.pathsep + os.environ["PATH"]

# Установи свой API-ключ OpenAI через переменную окружения или напрямую
openai.api_key = os.getenv("OPENAI_KEY")

# Инициализация инструмента для проверки грамматики
lt_tool = language_tool_python.LanguageTool('en-US')


def find_grammar_errors(text: str):
    matches = lt_tool.check(text)
    errors = []
    for match in matches:
        errors.append({
            "original": text[match.offset:match.offset + match.errorLength],
            "replacements": match.replacements,
            "message": match.message,
            "context": text[match.offset - 15: match.offset + 15],
            "rule_id": match.ruleId
        })
    return errors


def explain_correction(original: str, corrected: str, message: str):
    prompt = f"""
В предложении есть ошибка:
Оригинал: "{original}"
Исправлено: "{corrected}"
Ошибка: {message}

Объясни:
1. В чём ошибка;
2. Почему так неправильно;
3. Как правильно;
4. Какое правило применяется;
5. Приведи ещё один пример с объяснением.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system",
             "content": "Ты преподаватель английского языка, который объясняет ошибки понятно и детально."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return response["choices"][0]["message"]["content"]


def process_text(text: str):
    errors = find_grammar_errors(text)
    return errors
    explanations = []
    for err in errors:
        print(f'{err=}')
        original_phrase = err["original"]
        corrected_phrase = err["suggestion"]
        message = err["message"]

        full_original = text
        full_corrected = text.replace(original_phrase, corrected_phrase, 1)

        explanation = explain_correction(full_original, full_corrected, message)

        explanations.append({
            "original": original_phrase,
            "corrected": corrected_phrase,
            "message": message,
            "explanation": explanation
        })

    return explanations


# Пример запуска:
if __name__ == "__main__":
    user_text = input("Введите английский текст с ошибками: ")
    results = process_text(user_text)
    print(f'{results=}')
    for i, res in enumerate(results, 1):
        print(f"\n--- Ошибка {i} ---")
        print(f'{res}')
        # print(f"Оригинал: {res['original']}")
        # print(f"Исправлено: {res['corrected']}")
        # print(f"Описание: {res['message']}")
        # print(f"Объяснение: \n{res['explanation']}")
