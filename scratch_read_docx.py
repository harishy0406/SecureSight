import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            paragraphs = []
            for paragraph in tree.findall('.//w:p', namespaces):
                text_runs = []
                for run in paragraph.findall('.//w:r', namespaces):
                    text_node = run.find('w:t', namespaces)
                    if text_node is not None and text_node.text is not None:
                        text_runs.append(text_node.text)
                
                if text_runs:
                    paragraphs.append(''.join(text_runs))
                    
            return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error: {e}"

print("=== PRD ===")
print(extract_text_from_docx('SecureSight_PRD.docx'))
print("\n=== Tech Stack ===")
print(extract_text_from_docx('SecureSight_TechStack.docx'))
