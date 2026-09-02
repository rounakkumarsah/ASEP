with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\gemini.py', 'r', encoding='utf-8') as f: text = f.read()
target = 'url = f"/models/{request.model}:generateContent?key={self.api_key}"'
replacement = 'model_name = "gemini-1.5-pro-latest" if request.model == "gemini-1.5-pro" else request.model\n        url = f"/models/{model_name}:generateContent?key={self.api_key}"'
text = text.replace(target, replacement)
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\gemini.py', 'w', encoding='utf-8') as f: f.write(text)
