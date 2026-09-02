with open(r'C:\Users\sachi\ASEP\frontend\src\app\(dashboard)\playground\page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''                      <option value="deepseek-r1">OpenRouter (DeepSeek R1)</option>''',
'''                      <option value="deepseek-r1">OpenRouter (DeepSeek R1)</option>
                      <option value="openrouter/auto">OpenRouter Auto (Best Model)</option>
                      <option value="openrouter/free">OpenRouter Free (Zero Cost)</option>'''
)

with open(r'C:\Users\sachi\ASEP\frontend\src\app\(dashboard)\playground\page.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
